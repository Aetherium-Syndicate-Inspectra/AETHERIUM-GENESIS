export class ApprovalInbox {
  constructor({ inboxEl, countEl, onDecide, onView }) {
    this.inboxEl = inboxEl;
    this.countEl = countEl;
    this.onDecide = onDecide;
    this.onView = onView;
  }

  render(approvals) {
    this.countEl.textContent = `${approvals.length} PENDING`;
    if (approvals.length === 0) {
      this.inboxEl.innerHTML = '<div style="text-align: center; opacity: 0.5; margin-top: 2rem;">No pending approvals.</div>';
      return;
    }

    this.inboxEl.innerHTML = approvals.map(app => `
      <div class="approval-item">
          <span class="tier-tag tier-${app.tier}">Tier ${app.tier}</span>
          <div style="font-weight: bold; margin-bottom: 0.5rem;">${app.action_type}</div>
          <div style="font-size: 0.8rem; opacity: 0.7;">Actor: ${app.actor}</div>
          <div class="approval-actions">
              <button class="btn-approve" data-action="approve" data-id="${app.request_id}">APPROVE</button>
              <button class="btn-reject" data-action="reject" data-id="${app.request_id}">REJECT</button>
              <button class="btn-view" data-action="view" data-id="${app.request_id}">VIEW</button>
          </div>
      </div>`).join('');

    this.inboxEl.querySelectorAll('button[data-action]').forEach(btn => {
      const id = btn.dataset.id;
      const action = btn.dataset.action;
      if (action === 'approve') btn.onclick = () => this.onDecide(id, 'APPROVED');
      if (action === 'reject') btn.onclick = () => this.onDecide(id, 'REJECTED');
      if (action === 'view') btn.onclick = () => this.onView(id);
    });
  }
}
