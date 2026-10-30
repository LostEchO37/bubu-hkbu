const status = document.getElementById("status");

document.getElementById("inject").addEventListener("click", () => {
  status.textContent = "注入中…";
  chrome.runtime.sendMessage({ type: "bubu-inject-active" }, (res) => {
    if (chrome.runtime.lastError) {
      status.textContent = chrome.runtime.lastError.message;
      return;
    }
    status.textContent = res?.ok ? "已注入，请看页面右下角" : res?.error || "失败";
  });
});
