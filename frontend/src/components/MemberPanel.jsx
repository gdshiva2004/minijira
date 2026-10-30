import { useState } from "react";

const ROLES = ["Developer", "QA", "Manager"];

export default function MemberPanel({ members, onCreate }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState(ROLES[0]);

  async function submit(e) {
    e.preventDefault();
    const created = await onCreate({ name, role });
    if (created) {
      setName("");
      setRole(ROLES[0]);
    }
  }

  return (
    <section className="panel">
      <h2>Team</h2>
      <form onSubmit={submit}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Member name"
          maxLength={100}
          required
        />
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <button type="submit">Add member</button>
      </form>
      <ul className="members">
        {members.length === 0 && <li className="empty">No members yet</li>}
        {members.map((m) => (
          <li key={m.id}>
            <span>{m.name}</span>
            <span className={"badge role-" + m.role.toLowerCase()}>{m.role}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
