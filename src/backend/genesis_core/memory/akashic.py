import hashlib
import json
import os
import subprocess
import time
from typing import Dict, List, Optional


class JsonAkashicStore:
    """File-based store kept for local development and backward compatibility."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_db()

    def ensure_db(self) -> None:
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({"chain": [], "tenants": {}}, f)

    def _read(self) -> Dict:
        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "tenants" not in data:
            # Backward-compatible migration for old schema: {"chain": [...]}
            data = {"chain": data.get("chain", []), "tenants": {"global": data.get("chain", [])}}
        return data

    def _write(self, data: Dict) -> None:
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_chain(self, tenant_id: str) -> List[Dict]:
        data = self._read()
        if tenant_id == "global":
            return data.get("chain", [])
        return data.get("tenants", {}).get(tenant_id, [])

    def append_block(self, tenant_id: str, block: Dict) -> None:
        data = self._read()
        tenants = data.setdefault("tenants", {})
        tenant_chain = tenants.setdefault(tenant_id, [])
        tenant_chain.append(block)
        if tenant_id == "global":
            data["chain"] = tenant_chain
        self._write(data)


class FirestoreAkashicStore:
    """Firestore-backed store for stateless deployments (Cloud Run/Kubernetes)."""

    def __init__(self, collection: str = "akashic_records", project_id: Optional[str] = None):
        try:
            from google.cloud import firestore
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError(
                "google-cloud-firestore is required for Firestore backend. "
                "Install dependency and configure application default credentials."
            ) from exc

        self.client = firestore.Client(project=project_id)
        self.collection = collection

    def get_chain(self, tenant_id: str) -> List[Dict]:
        docs = (
            self.client.collection(self.collection)
            .document(tenant_id)
            .collection("chain")
            .order_by("timestamp")
            .stream()
        )
        return [doc.to_dict() for doc in docs]

    def append_block(self, tenant_id: str, block: Dict) -> None:
        (
            self.client.collection(self.collection)
            .document(tenant_id)
            .collection("chain")
            .document(block["hash"])
            .set(block)
        )


class AkashicRecords:
    """
    The Akashic Records immutable ledger.

    Backend selection:
    - json (default): writes to local disk.
    - firestore: persistent shared store for stateless infrastructure.
    """

    def __init__(
        self,
        db_path: str = "data/akashic_records.json",
        backend: Optional[str] = None,
        firestore_collection: str = "akashic_records",
        firestore_project_id: Optional[str] = None,
        default_tenant_id: str = "global",
    ):
        self.default_tenant_id = default_tenant_id
        self.backend = (backend or os.getenv("AKASHIC_BACKEND", "json")).lower()

        if self.backend not in ("json", "firestore"):
            raise ValueError(f"Unknown AKASHIC_BACKEND: '{self.backend}'. Supported: 'json', 'firestore'.")

        if self.backend == "firestore":
            self.store = FirestoreAkashicStore(
                collection=firestore_collection,
                project_id=firestore_project_id or os.getenv("GOOGLE_CLOUD_PROJECT"),
            )
        else:
            self.store = JsonAkashicStore(db_path=db_path)

    def _tenant(self, tenant_id: Optional[str]) -> str:
        return tenant_id or self.default_tenant_id

    def append_record(self, payload: Dict, tenant_id: Optional[str] = None) -> str:
        """Appends a new immutable record to a tenant-specific chain."""
        active_tenant = self._tenant(tenant_id)
        chain = self.store.get_chain(active_tenant)

        prev_hash = chain[-1]["hash"] if chain else "0" * 64
        timestamp = time.time()

        content = f"{timestamp}{json.dumps(payload, sort_keys=True)}{prev_hash}".encode()
        curr_hash = hashlib.sha256(content).hexdigest()

        block = {
            "timestamp": timestamp,
            "payload": payload,
            "prev_hash": prev_hash,
            "hash": curr_hash,
            "tenant_id": active_tenant,
        }

        self.store.append_block(active_tenant, block)
        return curr_hash

    def get_behavioral_history(
        self,
        actor_id: str,
        limit: int = 50,
        tenant_id: Optional[str] = None,
    ) -> List[Dict]:
        """Retrieves recent behavioral records for a specific actor and tenant."""
        history = []
        chain = self.store.get_chain(self._tenant(tenant_id))

        for block in reversed(chain):
            payload = block.get("payload", {})
            actor = payload.get("actor") or payload.get("origin_agent")
            if not actor and "audit" in payload:
                actor = payload["audit"].get("actor")

            if actor == actor_id:
                history.append(block)
            if len(history) >= limit:
                break

        return history

    def get_recent_audits(self, limit: int = 20, tenant_id: Optional[str] = None) -> List[Dict]:
        """Retrieves recent audit logs for a tenant."""
        audits = []
        chain = self.store.get_chain(self._tenant(tenant_id))

        for block in reversed(chain):
            payload = block.get("payload", {})
            if payload.get("type") == "audit_log" or payload.get("action") == "PERMISSION_CHECK":
                audits.append(block)
            if len(audits) >= limit:
                break

        return audits

    def verify_hash_chain(self, tenant_id: Optional[str] = None) -> bool:
        """Verifies cryptographic integrity for a tenant chain."""
        chain = self.store.get_chain(self._tenant(tenant_id))
        if not chain:
            return True

        prev_hash = "0" * 64
        for block in chain:
            payload = block["payload"]
            timestamp = block["timestamp"]
            ph = block["prev_hash"]

            if ph != prev_hash:
                return False

            content = f"{timestamp}{json.dumps(payload, sort_keys=True)}{ph}".encode()
            curr_hash = hashlib.sha256(content).hexdigest()

            if curr_hash != block["hash"]:
                return False

            prev_hash = curr_hash

        return True

    def check_temporal_consistency(self, tenant_id: Optional[str] = None) -> bool:
        """Verifies timestamps are monotonically increasing per tenant."""
        chain = self.store.get_chain(self._tenant(tenant_id))

        last_ts = 0.0
        for block in chain:
            if block["timestamp"] < last_ts:
                return False
            last_ts = block["timestamp"]
        return True


class GitMemorySystem:
    """
    Interface to the PanGenesis (Git) Repository.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: List[str]) -> str:
        try:
            subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def verify_integrity(self) -> bool:
        """Checks if the git repository is healthy."""
        if not self._run_git(["rev-parse", "--is-inside-work-tree"]):
            return False

        fsck = self._run_git(["fsck", "--no-dangling"])
        return "error" not in fsck.lower()

    def get_current_commit_hash(self) -> str:
        return self._run_git(["rev-parse", "HEAD"])
