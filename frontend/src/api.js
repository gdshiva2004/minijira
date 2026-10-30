const BASE = "/api";
const TOKEN_KEY = "minijira_token";

let unauthorizedHandler = null;

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

async function request(method, path, body) {
  const headers = {};
  const token = getToken();
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = "Bearer " + token;

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
    if (res.status === 401 && token && unauthorizedHandler) unauthorizedHandler();
    throw new Error(data && data.error ? data.error : "Request failed (" + res.status + ")");
  }
  return data;
}

export const api = {
  signup: (fields) => request("POST", "/auth/signup", fields),
  login: (fields) => request("POST", "/auth/login", fields),
  me: () => request("GET", "/auth/me"),
  listMembers: () => request("GET", "/members"),
  listTasks: (status) =>
    request("GET", "/tasks" + (status ? "?status=" + encodeURIComponent(status) : "")),
  createTask: (task) => request("POST", "/tasks", task),
  setAssignee: (taskId, assigneeId) =>
    request("PUT", "/tasks/" + taskId + "/assignee", { assignee_id: assigneeId }),
  setStatus: (taskId, status) =>
    request("PATCH", "/tasks/" + taskId + "/status", { status }),
};
