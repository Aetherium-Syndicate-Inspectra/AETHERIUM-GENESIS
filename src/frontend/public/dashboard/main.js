import { ApprovalInbox } from './approvalInbox.js';
import { ActionPreview } from './actionPreview.js';
import { GemPanel } from './gemPanel.js';

class GovernanceManager {
  constructor() {
    this.inbox = new ApprovalInbox({
      inboxEl: document.getElementById('approval-inbox'),
      countEl: document.getElementById('pending-count'),
      onDecide: (id, d) => this.decide(id, d),
      onView: (id) => this.view(id)
    });
    this.preview = new ActionPreview({ previewEl: document.getElementById('action-preview') });
    this.gems = new GemPanel({ gemEl: document.getElementById('gem-list') });
    this.preview.clear();
    this.poll();
    this.fetchGems();
  }

  async poll() {
    setInterval(() => this.fetchApprovals(), 5000);
    this.fetchApprovals();
  }

  async fetchApprovals() {
    try {
      const res = await fetch('/governance/approvals');
      const data = await res.json();
      this.inbox.render(data);
    } catch (e) { console.error('Gov Link Failed', e); }
  }

  async fetchGems() {
    try {
      const res = await fetch('/governance/gems');
      const data = await res.json();
      this.gems.render(data.gems || []);
    } catch (e) { console.error('Gem Link Failed', e); }
  }

  async decide(id, decision) {
    await fetch('/governance/decide', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id: id, decision })
    });
    this.fetchApprovals();
    this.preview.clear('Action processed.');
  }

  async view(id) {
    const res = await fetch('/governance/approvals');
    const approvals = await res.json();
    const app = approvals.find(a => a.request_id === id);
    if (app) this.preview.renderApproval(app);
  }
}

window.governanceManager = new GovernanceManager();
