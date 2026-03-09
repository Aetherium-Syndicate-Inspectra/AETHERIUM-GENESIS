export class ActionPreview {
  constructor({ previewEl }) {
    this.previewEl = previewEl;
  }

  clear(message = 'Select a pending action to preview impact.') {
    this.previewEl.innerHTML = `<div style="opacity: 0.5;">${message}</div>`;
  }

  renderApproval(approval) {
    this.previewEl.innerHTML = `
      <div style="color: var(--accent-cyan); margin-bottom: 1rem;">>>> PREVIEW: ${approval.action_type}</div>
      <div>Intent ID: ${approval.intent_id}</div>
      <div class="diff-view">
          ${JSON.stringify(approval.preview_data, null, 2)}
      </div>
    `;
  }
}
