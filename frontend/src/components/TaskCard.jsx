import Avatar from "./Avatar";

const STATUSES = ["To Do", "In Progress", "Done"];

export default function TaskCard({ task, members, busy, onAssign, onStatus }) {
  function nameOf(id) {
    const member = members.find((m) => m.id === id);
    return member ? member.name : "Unknown member";
  }

  const assignee = members.find((m) => m.id === task.assignee_id);

  return (
    <article className={busy ? "card busy" : "card"}>
      <div className="card-head">
        <h3>{task.title}</h3>
        <span className={"badge priority-" + task.priority.toLowerCase()}>{task.priority}</span>
      </div>
      <p className="description">{task.description}</p>

      <div className="assignee">
        {assignee ? <Avatar name={assignee.name} size={26} /> : <span className="avatar empty-avatar" />}
        <select
          value={task.assignee_id || ""}
          disabled={busy}
          aria-label="Assignee"
          onChange={(e) => onAssign(task, e.target.value || null)}
        >
          <option value="">Unassigned</option>
          {members.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name} ({m.role})
            </option>
          ))}
        </select>
      </div>

      <div className="actions">
        {STATUSES.filter((s) => s !== task.status).map((s) => (
          <button type="button" className="secondary small" key={s} disabled={busy} onClick={() => onStatus(task, s)}>
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
                <strong>{nameOf(h.changed_by)}</strong> moved it from {h.from} to {h.to}
                <span className="when">{new Date(h.changed_at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}
