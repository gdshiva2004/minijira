import Avatar from "./Avatar";

export default function TeamPanel({ members, currentId }) {
  return (
    <section className="panel">
      <h2>
        Team <span className="count">{members.length}</span>
      </h2>
      <ul className="members">
        {members.length === 0 && <li className="empty">No members yet</li>}
        {members.map((member) => (
          <li key={member.id}>
            <Avatar name={member.name} />
            <span className="member-name">
              {member.name}
              {member.id === currentId && <span className="you">You</span>}
            </span>
            <span className={"badge role-" + member.role.toLowerCase()}>{member.role}</span>
          </li>
        ))}
      </ul>
      <p className="hint">New teammates join by signing up.</p>
    </section>
  );
}
