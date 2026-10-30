const DEFAULT_APP_URL = "http://localhost:8501";
const input = document.getElementById("appUrl");
const status = document.getElementById("status");

chrome.storage.sync.get({ bubu_app_url: DEFAULT_APP_URL }, (data) => {
  input.value = data.bubu_app_url || DEFAULT_APP_URL;
});

document.getElementById("save").addEventListener("click", () => {
  const url = (input.value || "").trim().replace(/\/$/, "") || DEFAULT_APP_URL;
  chrome.storage.sync.set({ bubu_app_url: url }, () => {
    status.textContent = "已保存";
  });
});
