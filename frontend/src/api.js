const BASE = "/api";

async function request(method, path, body, actorId) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (actorId) headers["X-Member-Id"] = actorId;

  let res;
  try {
    res = await fetch(BASE + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the API. Is the Flask server running on port 5000?");
  }

  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    throw new Error(data && data.error ? data.error : "Request failed (" + res.status + ")");
  }
  return data;
}

export const api = {
  listMembers: () => request("GET", "/members"),
  createMember: (member) => request("POST", "/members", member),
  listTasks: (status) =>
    request("GET", "/tasks" + (status ? "?status=" + encodeURIComponent(status) : "")),
  createTask: (task) => request("POST", "/tasks", task),
  setAssignee: (taskId, assigneeId) =>
    request("PUT", "/tasks/" + taskId + "/assignee", { assignee_id: assigneeId }),
  setStatus: (taskId, status, actorId) =>
    request("PATCH", "/tasks/" + taskId + "/status", { status }, actorId),
};
