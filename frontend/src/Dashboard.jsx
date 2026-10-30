import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import Avatar from "./components/Avatar";
import TaskCard from "./components/TaskCard";
import TaskForm from "./components/TaskForm";
import TeamPanel from "./components/TeamPanel";

const STATUSES = ["To Do", "In Progress", "Done"];

export default function Dashboard({ user, onLogout }) {
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

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
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(""), 3500);
    return () => clearTimeout(timer);
  }, [notice]);

  async function refresh() {
    setError("");
    await Promise.all([loadMembers(), loadTasks()]);
  }

  async function addTask(task) {
    setError("");
    try {
      await api.createTask(task);
      await loadTasks();
      setNotice("Task created");
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    }
  }

  async function assign(task, memberId) {
    setError("");
    setBusyId(task.id);
    try {
      await api.setAssignee(task.id, memberId);
      const member = members.find((m) => m.id === memberId);
      setNotice(member ? "Assigned to " + member.name : "Task unassigned");
    } catch (e) {
      setError(e.message);
    }
    await loadTasks();
    setBusyId(null);
  }

  async function changeStatus(task, status) {
    setError("");
    setBusyId(task.id);
    try {
      await api.setStatus(task.id, status);
      setNotice("Moved to " + status);
    } catch (e) {
      setError(e.message);
    }
    await loadTasks();
    setBusyId(null);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">M</span>
          <span className="brand-name">Mini-Jira</span>
        </div>
        <div className="topbar-controls">
          <label className="inline-field">
            Status
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">All</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="secondary" onClick={refresh}>
            Refresh
          </button>
          <div className="user-chip">
            <Avatar name={user.name} size={30} />
            <div className="user-text">
              <strong>{user.name}</strong>
              <span className={"badge role-" + user.role.toLowerCase()}>{user.role}</span>
            </div>
          </div>
          <button type="button" className="ghost" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>

      {error && (
        <div className="banner error page-banner" role="alert">
          <span>{error}</span>
          <button type="button" className="ghost small" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}

      <main className="layout">
        <aside className="sidebar">
          <TaskForm onCreate={addTask} />
          <TeamPanel members={members} currentId={user.id} />
        </aside>

        <section className="board">
          {STATUSES.map((status) => {
            const column = tasks.filter((t) => t.status === status);
            return (
              <div className={"column column-" + status.toLowerCase().replace(" ", "-")} key={status}>
                <h2>
                  <span className="dot" />
                  {status}
                  <span className="count">{column.length}</span>
                </h2>
                {loading && <p className="empty">Loading...</p>}
                {!loading && column.length === 0 && <p className="empty">Nothing here yet</p>}
                {column.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    members={members}
                    busy={busyId === task.id}
                    onAssign={assign}
                    onStatus={changeStatus}
                  />
                ))}
              </div>
            );
          })}
        </section>
      </main>

      {notice && (
        <div className="toast" role="status">
          {notice}
        </div>
      )}
    </div>
  );
}
