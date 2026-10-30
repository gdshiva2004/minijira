import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import MemberPanel from "./components/MemberPanel";
import TaskForm from "./components/TaskForm";
import TaskCard from "./components/TaskCard";

const STATUSES = ["To Do", "In Progress", "Done"];

export default function App() {
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState("");
  const [actorId, setActorId] = useState("");
  const [error, setError] = useState("");

  const loadMembers = useCallback(async () => {
    try {
      setMembers(await api.listMembers());
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const loadTasks = useCallback(async () => {
    try {
      setTasks(await api.listTasks(filter));
    } catch (e) {
      setError(e.message);
    }
  }, [filter]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  async function addMember(member) {
    setError("");
    try {
      await api.createMember(member);
      await loadMembers();
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    }
  }

  async function addTask(task) {
    setError("");
    try {
      await api.createTask(task);
      await loadTasks();
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    }
  }

  async function assign(taskId, memberId) {
    setError("");
    try {
      await api.setAssignee(taskId, memberId);
    } catch (e) {
      setError(e.message);
    }
    await loadTasks();
  }

  async function changeStatus(taskId, status) {
    setError("");
    if (!actorId) {
      setError("Choose who you are acting as before changing a status.");
      return;
    }
    try {
      await api.setStatus(taskId, status, actorId);
    } catch (e) {
      setError(e.message);
    }
    await loadTasks();
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Mini-Jira</h1>
        <div className="topbar-controls">
          <label>
            Acting as
            <select value={actorId} onChange={(e) => setActorId(e.target.value)}>
              <option value="">Choose a member</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.role})
                </option>
              ))}
            </select>
          </label>
          <label>
            Filter
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">All statuses</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={loadTasks}>
            Refresh
          </button>
        </div>
      </header>

      {error && (
        <div className="error" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}

      <main className="layout">
        <aside className="sidebar">
          <MemberPanel members={members} onCreate={addMember} />
          <TaskForm onCreate={addTask} />
        </aside>

        <section className="board">
          {STATUSES.map((status) => {
            const column = tasks.filter((t) => t.status === status);
            return (
              <div className="column" key={status}>
                <h2>
                  {status} <span className="count">{column.length}</span>
                </h2>
                {column.length === 0 && <p className="empty">No tasks</p>}
                {column.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    members={members}
                    onAssign={assign}
                    onStatus={changeStatus}
                  />
                ))}
              </div>
            );
          })}
        </section>
      </main>
    </div>
  );
}
