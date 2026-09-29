document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("download-btn");
  if (!button) return;

  button.addEventListener("click", async () => {
    const url = button.dataset.downloadUrl;
    const filename = button.dataset.filename || "comic.pdf";
    button.disabled = true;
    button.textContent = "Preparing PDF…";

    try {
      const response = await fetch(url, { credentials: "same-origin" });
      if (!response.ok) throw new Error(`Download failed (${response.status})`);
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
      window.location.assign(`/export-success?filename=${encodeURIComponent(filename)}`);
    } catch (error) {
      console.error(error);
      window.alert("PDF download failed. Please try again or use the Download Again link on the export page.");
      button.disabled = false;
      button.textContent = "📥 Download Your Comic as PDF";
    }
  });
});
