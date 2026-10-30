import { useState } from "react";

const PRIORITIES = ["Low", "Medium", "High"];

export default function TaskForm({ onCreate }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("Medium");

  async function submit(e) {
    e.preventDefault();
    const created = await onCreate({ title, description, priority });
    if (created) {
      setTitle("");
      setDescription("");
      setPriority("Medium");
    }
  }

  return (
    <section className="panel">
      <h2>New task</h2>
      <form onSubmit={submit}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title"
          maxLength={200}
          required
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description"
          rows={3}
          maxLength={2000}
          required
        />
        <select value={priority} onChange={(e) => setPriority(e.target.value)}>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p} priority
            </option>
          ))}
        </select>
        <button type="submit">Create task</button>
      </form>
    </section>
  );
}
