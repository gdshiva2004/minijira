import { useState } from "react";

const PRIORITIES = ["Low", "Medium", "High"];

export default function TaskForm({ onCreate }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("Medium");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    const created = await onCreate({ title, description, priority });
    setBusy(false);
    if (created) {
      setTitle("");
      setDescription("");
      setPriority("Medium");
    }
  }

  return (
    <section className="panel">
      <h2>New task</h2>
      <form onSubmit={submit} className="stack">
        <label className="field">
          Title
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="What needs doing?"
            maxLength={200}
            required
          />
        </label>
        <label className="field">
          Description
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add a few details"
            rows={3}
            maxLength={2000}
            required
          />
        </label>
        <label className="field">
          Priority
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="primary" disabled={busy}>
          {busy ? "Creating..." : "Create task"}
        </button>
      </form>
    </section>
  );
}
