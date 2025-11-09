import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, time, csv, json
import speedtest

def run_test(labels, progress, status_label, btn):
    def worker():
        try:
            btn.config(state="disabled")
            progress["value"] = 0
            status_label.config(text="Preparing servers...")

            st = speedtest.Speedtest()
            st.get_servers([])
            st.get_best_server()

            # Ping
            status_label.config(text="Measuring ping...")
            ping = st.results.ping
            labels["ping"].config(text=f"Ping: {round(ping,2)} ms")
            progress["value"] = 25
            time.sleep(0.5)

            # Download
            status_label.config(text="Measuring download speed...")
            download = st.download() / (1024*1024)
            labels["download"].config(text=f"Download: {round(download,2)} Mbps")
            progress["value"] = 60
            time.sleep(0.5)

            # Upload
            status_label.config(text="Measuring upload speed...")
            upload = st.upload(pre_allocate=False) / (1024*1024)
            labels["upload"].config(text=f"Upload: {round(upload,2)} Mbps")
            progress["value"] = 100

            # Other info
            labels["server"].config(text=f"Server: {st.results.server.get('name')}")
            labels["sponsor"].config(text=f"Sponsor: {st.results.server.get('sponsor')}")
            labels["time"].config(text=f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

            status_label.config(text="✔ Test completed successfully")
            status_label.config(fg="#0078D7")  # Metro blue
        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_label.config(text="✖ Error during test", fg="red")
        finally:
            btn.config(state="normal")

    threading.Thread(target=worker, daemon=True).start()

def save_results(labels, fmt):
    data = {k: v.cget("text") for k,v in labels.items()}
    if not data:
        messagebox.showwarning("Warning", "No results to save.")
        return
    filetypes = [("CSV files","*.csv")] if fmt=="csv" else [("JSON files","*.json")]
    f = filedialog.asksaveasfilename(defaultextension=filetypes[0][1], filetypes=filetypes)
    if not f: return
    with open(f, "w", newline="", encoding="utf-8") as out:
        if fmt=="csv":
            writer = csv.writer(out)
            writer.writerow(data.keys())
            writer.writerow(data.values())
        else:
            json.dump(data, out, ensure_ascii=False, indent=2)
    messagebox.showinfo("Saved", f"Results saved to {f}")

def main():
    root = tk.Tk()
    root.title("SpeedTest Metro UI")
    root.geometry("520x420")
    root.configure(bg="#f2f2f2")

    # Metro style
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 11), padding=8, background="#0078D7", foreground="white")
    style.map("TButton", background=[("active","#005A9E")])
    style.configure("TProgressbar", thickness=20, troughcolor="#e5e5e5", background="#0078D7")

    # Status label
    status_label = tk.Label(root, text="Click 'Start Test' to begin", font=("Segoe UI", 11),
                            bg="#f2f2f2", fg="#333")
    status_label.pack(pady=10)

    # Progress bar
    progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress.pack(pady=5)

    # Result labels
    labels = {}
    for key in ["ping","download","upload","server","sponsor","time"]:
        labels[key] = tk.Label(root, text=f"{key.capitalize()}: -", font=("Segoe UI", 12),
                               bg="#f2f2f2", fg="#111", anchor="w")
        labels[key].pack(fill="x", padx=20, pady=4)

    # Buttons
    frame = tk.Frame(root, bg="#f2f2f2")
    frame.pack(pady=15)

    btn_test = ttk.Button(frame, text="▶ Start Test",
                          command=lambda: run_test(labels, progress, status_label, btn_test))
    btn_csv = ttk.Button(frame, text="💾 Save CSV", command=lambda: save_results(labels,"csv"))
    btn_json = ttk.Button(frame, text="💾 Save JSON", command=lambda: save_results(labels,"json"))

    btn_test.grid(row=0, column=0, padx=8)
    btn_csv.grid(row=0, column=1, padx=8)
    btn_json.grid(row=0, column=2, padx=8)

    root.mainloop()

if __name__ == "__main__":
    main()
