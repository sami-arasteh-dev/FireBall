import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, time, csv, json
import speedtest

# --- 🛠️ ثابت‌ها ---
# تبدیل بایت بر ثانیه (Bytes/s) به مگابیت بر ثانیه (Mbits/s)
MBITS_PER_BYTE = 8 / (1024 * 1024) 

class SpeedTestApp:
    def __init__(self, master):
        self.master = master
        master.title("SpeedTest Monitor")
        master.geometry("520x420")
        master.configure(bg="#f2f2f2")

        # وضعیت ذخیره (برای فعال/غیرفعال‌سازی دکمه‌های ذخیره)
        self.test_successful = False

        # --- Metro style ---
        self._setup_style()
        
        # --- UI Elements ---
        self.status_label = tk.Label(master, text="Click 'Start Test' to begin", font=("Segoe UI", 11), bg="#f2f2f2", fg="#333")
        self.status_label.pack(pady=10)

        self.progress = ttk.Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=5)
        
        # Result labels
        self.labels = {}
        for key in ["ping", "download", "upload", "server", "sponsor", "time"]:
            self.labels[key] = tk.Label(master, text=f"{key.capitalize()}: -", font=("Segoe UI", 12), bg="#f2f2f2", fg="#111", anchor="w")
            self.labels[key].pack(fill="x", padx=20, pady=4)
        
        # Buttons
        self.frame = tk.Frame(master, bg="#f2f2f2")
        self.frame.pack(pady=15)

        self.btn_test = ttk.Button(self.frame, text="▶ Start Test", command=self._start_test_thread)
        self.btn_csv = ttk.Button(self.frame, text="💾 Save CSV", command=lambda: self._save_results("csv"), state="disabled")
        self.btn_json = ttk.Button(self.frame, text="💾 Save JSON", command=lambda: self._save_results("json"), state="disabled")

        self.btn_test.grid(row=0, column=0, padx=8)
        self.btn_csv.grid(row=0, column=1, padx=8)
        self.btn_json.grid(row=0, column=2, padx=8)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11), padding=8, background="#0078D7", foreground="white")
        style.map("TButton", background=[("active", "#005A9E")])
        style.configure("TProgressbar", thickness=20, troughcolor="#e5e5e5", background="#0078D7")

    def _update_ui_after_test(self, success, message=""):
        """به‌روزرسانی UI پس از اتمام/شکست تست"""
        self.btn_test.config(state="normal")
        self.test_successful = success
        
        if success:
            self.status_label.config(text="✔ Test completed successfully", fg="#0078D7")
            self.btn_csv.config(state="normal")
            self.btn_json.config(state="normal")
        else:
            self.status_label.config(text=f"✖ Error: {message}", fg="red")
            self.btn_csv.config(state="disabled")
            self.btn_json.config(state="disabled")

    def _update_progress(self, progress_type, current_progress):
        """تابع Callback برای به‌روزرسانی Progressbar در طول تست"""
        # (Callback value is in Bytes. Max 100000000 for 100MB)
        if progress_type == 'download':
            # تبدیل به مقیاس 0 تا 100
            value = 10 + (current_progress / 1000000)
            self.progress["value"] = value
        elif progress_type == 'upload':
            # تبدیل به مقیاس 50 تا 100
            value = 50 + (current_progress / 1000000)
            self.progress["value"] = value
        self.master.update_idletasks() # ضروری برای نمایش به‌روزرسانی

    def _worker(self):
        """منطق اصلی تست در یک ترد جداگانه"""
        try:
            self.btn_test.config(state="disabled")
            self.btn_csv.config(state="disabled")
            self.btn_json.config(state="disabled")
            self.progress["value"] = 0
            self.status_label.config(text="Preparing servers...")

            st = speedtest.Speedtest()
            st.get_servers([])
            
            # 1. Best Server & Ping
            server = st.get_best_server()
            self.status_label.config(text=f"Measuring ping to {server.get('host')}...")
            ping = st.results.ping
            self.labels["ping"].config(text=f"Ping: {round(ping, 2)} ms")
            self.progress["value"] = 10 # 10% برای Ping
            
            # 2. Download
            self.status_label.config(text="Measuring download speed (using callback)...")
            # استفاده از callback برای به‌روزرسانی Progressbar در طول دانلود
            download_bytes = st.download(callback=lambda current, total: self._update_progress('download', current / total * 40)) # 10% تا 50%
            download_mbps = download_bytes * MBITS_PER_BYTE
            self.labels["download"].config(text=f"Download: {round(download_mbps, 2)} Mbps")
            self.progress["value"] = 50 # 50% بعد از اتمام دانلود
            
            # 3. Upload
            self.status_label.config(text="Measuring upload speed (using callback)...")
            # استفاده از callback برای به‌روزرسانی Progressbar در طول آپلود
            upload_bytes = st.upload(pre_allocate=False, callback=lambda current, total: self._update_progress('upload', current / total * 50)) # 50% تا 100%
            upload_mbps = upload_bytes * MBITS_PER_BYTE
            self.labels["upload"].config(text=f"Upload: {round(upload_mbps, 2)} Mbps")
            self.progress["value"] = 100 # 100% بعد از اتمام آپلود

            # 4. Other info
            self.labels["server"].config(text=f"Server: {st.results.server.get('name', 'N/A')}")
            self.labels["sponsor"].config(text=f"Sponsor: {st.results.server.get('sponsor', 'N/A')}")
            self.labels["time"].config(text=f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

            self._update_ui_after_test(True)

        except speedtest.SpeedtestException as e:
            # مدیریت خطاهای خاص speedtest (مانند No servers found)
            messagebox.showerror("Network Error", f"Speedtest failed: {str(e)}")
            self._update_ui_after_test(False, str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._update_ui_after_test(False, str(e))

    def _start_test_thread(self):
        """شروع تست در یک ترد جداگانه برای جلوگیری از فریز شدن UI"""
        # ریست کردن وضعیت‌های ذخیره
        for key in ["ping", "download", "upload", "server", "sponsor", "time"]:
             self.labels[key].config(text=f"{key.capitalize()}: -")

        threading.Thread(target=self._worker, daemon=True).start()

    def _save_results(self, fmt):
        """ذخیره نتایج در فرمت CSV یا JSON"""
        if not self.test_successful:
            messagebox.showwarning("Warning", "Test failed or not yet completed. Cannot save results.")
            return

        # استخراج داده‌ها با حذف پیشوند (e.g., "Ping: 50 ms" -> "50 ms")
        data = {k: v.cget("text").split(': ', 1)[-1] for k, v in self.labels.items()}

        filetypes = [("CSV files", "*.csv")] if fmt == "csv" else [("JSON files", "*.json")]
        f = filedialog.asksaveasfilename(defaultextension=filetypes[0][1], filetypes=filetypes)
        if not f: return

        try:
            with open(f, "w", newline="", encoding="utf-8") as out:
                if fmt == "csv":
                    writer = csv.writer(out)
                    writer.writerow(data.keys())
                    writer.writerow(data.values())
                else:
                    json.dump(data, out, ensure_ascii=False, indent=2)
            messagebox.showinfo("Saved", f"Results saved to {f}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file: {str(e)}")


def main():
    root = tk.Tk()
    app = SpeedTestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
