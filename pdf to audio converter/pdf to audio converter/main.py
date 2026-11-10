import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PyPDF2 import PdfReader
from gtts import gTTS
import subprocess
import threading

def clean_text(text):
    # Remove any invalid characters
    return ''.join(char for char in text if ord(char) < 0x10000)

def select_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
    listbox.delete(0, tk.END)
    for file in file_paths:
        listbox.insert(tk.END, file)

def preview_text():
    file_path = listbox.get(tk.ACTIVE)
    if not file_path:
        messagebox.showerror("Error", "Please select a PDF file first")
        return

    reader = PdfReader(file_path)
    num_pages = len(reader.pages)
    start = simpledialog.askinteger("Start Page", f"Enter start page (1-{num_pages}):", minvalue=1, maxvalue=num_pages)
    if not start:
        return
        
    end = simpledialog.askinteger("End Page", f"Enter end page ({start}-{num_pages}):", minvalue=start, maxvalue=num_pages)
    if not end:
        return

    text = ""
    for i in range(start-1, end):
        page_text = reader.pages[i].extract_text() or ""
        text += clean_text(page_text) + "\n\n"

    preview.delete("1.0", tk.END)
    preview.insert(tk.END, text)
    
    # Save text file automatically
    txt_file = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        initialfile=f"{os.path.splitext(os.path.basename(file_path))[0]}_pages_{start}_to_{end}.txt"
    )
    
    if txt_file:
        try:
            with open(txt_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(text)
            messagebox.showinfo("Success", f"Text file saved to: {txt_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save text file: {str(e)}")

def convert_to_audio():
    file_path = listbox.get(tk.ACTIVE)
    if not file_path:
        messagebox.showerror("Error", "Please select a PDF file first")
        return

    def conversion_thread():
        try:
            # Extract text from entire PDF
            reader = PdfReader(file_path)
            text = ""
            for i in range(len(reader.pages)):
                page_text = reader.pages[i].extract_text() or ""
                text += clean_text(page_text)

            if not text.strip():
                messagebox.showerror("Error", "No text could be extracted from the PDF")
                return

            # Save text file
            txt_file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=f"{os.path.splitext(os.path.basename(file_path))[0]}.txt"
            )
            
            if txt_file:
                try:
                    with open(txt_file, "w", encoding="utf-8", errors="replace") as f:
                        f.write(text)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save text file: {str(e)}")
                    return

            # Create TTS
            speed = slow_var.get()
            tts = gTTS(text=text, lang='en', slow=speed)

            # Save MP3
            mp3_file = filedialog.asksaveasfilename(
                defaultextension=".mp3",
                filetypes=[("MP3 files", "*.mp3")],
                initialfile=f"{os.path.splitext(os.path.basename(file_path))[0]}.mp3"
            )
            
            if not mp3_file:
                return

            tts.save(mp3_file)

            # Convert to WAV
            wav_file = mp3_file.replace(".mp3", ".wav")
            try:
                subprocess.run(["ffmpeg", "-i", mp3_file, "-y", wav_file], 
                             capture_output=True, check=True)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to convert to WAV: {e.stderr.decode()}")
                return

            messagebox.showinfo("Success", f"Conversion complete!\nText file: {txt_file}\nMP3: {mp3_file}\nWAV: {wav_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    # Start conversion in a separate thread
    thread = threading.Thread(target=conversion_thread)
    thread.daemon = True
    thread.start()

# ==== GUI ====
root = tk.Tk()
root.title("PDF to Audio Converter")

# Create widgets
tk.Button(root, text="Select PDF Files", command=select_files).pack(pady=5)
listbox = tk.Listbox(root, width=60)
listbox.pack(pady=5)

tk.Button(root, text="Preview Text", command=preview_text).pack(pady=5)
preview = tk.Text(root, height=10, width=60)
preview.pack(pady=5)

tk.Label(root, text="Output Format: MP3 (default) or WAV (using ffmpeg)").pack()

slow_var = tk.BooleanVar()
tk.Checkbutton(root, text="Slow Speed", variable=slow_var).pack()

tk.Button(root, text="Convert to Audio", command=convert_to_audio).pack(pady=5)

root.mainloop()
