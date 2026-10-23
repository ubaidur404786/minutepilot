export function fileKind(file) {
  const type = file.type || "";
  if (type.startsWith("audio/") || /\.(wav|mp3|m4a|ogg|webm|flac|aac|mp4)$/i.test(file.name)) return "audio";
  if (type.startsWith("image/") || /\.(jpe?g|png|webp|heic|bmp)$/i.test(file.name)) return "image";
  return "other";
}

export function clock(seconds) {
  return new Date(seconds * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function duration(seconds) {
  if (!seconds && seconds !== 0) return "";
  if (seconds < 60) return `${Math.round(seconds)} s`;
  const m = Math.floor(seconds / 60);
  return `${m} min ${Math.round(seconds - m * 60)} s`;
}

// Sidebar groups, like other chat apps: Today, Yesterday, Previous 7 days, Older
export function dayGroup(seconds) {
  const d = new Date(seconds * 1000);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = (today - new Date(d.getFullYear(), d.getMonth(), d.getDate())) / 86400000;
  if (diff <= 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff < 7) return "Previous 7 days";
  return "Older";
}

export const SOURCE_LABEL = { page: "Chat page", n8n: "n8n", python: "Python service" };
