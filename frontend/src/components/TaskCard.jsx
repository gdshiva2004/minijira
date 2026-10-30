const STATUSES = ["To Do", "In Progress", "Done"];

export default function TaskCard({ task, members, onAssign, onStatus }) {
  function nameOf(id) {
    const member = members.find((m) => m.id === id);
    return member ? member.name : "Unknown member";
  }

  return (
    <article className="card">
      <div className="card-head">
        <h3>{task.title}</h3>
        <span className={"badge priority-" + task.priority.toLowerCase()}>{task.priority}</span>
      </div>
      <p className="description">{task.description}</p>

      <label className="field">
        Assignee
        <select
          value={task.assignee_id || ""}
          onChange={(e) => onAssign(task.id, e.target.value || null)}
        >
          <option value="">Unassigned</option>
          {members.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name} ({m.role})
            </option>
          ))}
        </select>
      </label>

      <div className="actions">
        {STATUSES.filter((s) => s !== task.status).map((s) => (
          <button type="button" key={s} onClick={() => onStatus(task.id, s)}>
            Move to {s}
          </button>
        ))}
      </div>

      {task.status_history.length > 0 && (
        <details className="history">
          <summary>History ({task.status_history.length})</summary>
          <ul>
            {task.status_history.map((h, i) => (
              <li key={i}>
                {h.from} to {h.to} by {nameOf(h.changed_by)} on{" "}
                {new Date(h.changed_at).toLocaleString()}
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}
