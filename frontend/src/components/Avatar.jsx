function initials(name) {
  const parts = name.trim().split(/\s+/);
  const letters = parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : parts[0].slice(0, 2);
  return letters.toUpperCase();
}

function hue(name) {
  let total = 0;
  for (const ch of name) total += ch.charCodeAt(0);
  return (total * 37) % 360;
}

export default function Avatar({ name, size = 28 }) {
  return (
    <span
      className="avatar"
      style={{
        width: size,
        height: size,
        fontSize: Math.round(size * 0.4),
        background: "hsl(" + hue(name) + " 55% 42%)",
      }}
      aria-hidden="true"
    >
      {initials(name)}
    </span>
  );
}
