const API = (window.API_BASE || "");

async function jget(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(path + " -> " + r.status);
  return r.json();
}
async function jpost(path, body) {
  const r = await fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(path + " -> " + r.status + " " + (await r.text()).slice(0, 200));
  return r.json();
}
async function upload(kind, file) {
  const fd = new FormData();
  fd.append("kind", kind); fd.append("file", file);
  const r = await fetch(API + "/api/upload", { method: "POST", body: fd });
  if (!r.ok) throw new Error("upload failed " + r.status);
  return r.json();
}
async function download(fmt, title, text) {
  const r = await fetch(API + "/api/export", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title, text, fmt }) });
  if (!r.ok) throw new Error("export failed");
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "statement_of_purpose." + fmt; a.click();
}
