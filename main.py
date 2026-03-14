import customtkinter as ctk
from tkcalendar import DateEntry
from tkcalendar import Calendar
from tkinter import messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sqlite3
import matplotlib
import csv
from tkinter import filedialog


matplotlib.rcParams['font.family'] = 'MS Gothic'

DB_FILE = "study.db"
WINDOW_TITLE = "学習記録アプリ"

# データベース管理クラス

class DBManager:

    def __init__(self,db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS study(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                subject TEXT,
                time INTEGER
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)

        self.conn.commit()

        default_subjects = ["Python", "SQL", "アルゴリズム", "英語"]

        for s in default_subjects:
            try:
               self.cursor.execute("INSERT INTO subjects(name) VALUES(?)",(s,))
            except:
               pass

        self.conn.commit()

    def get_subjects(self):
        self.cursor.execute("SELECT name FROM subjects")
        return [row[0] for row in self.cursor.fetchall()]
    
    def add_subject(self,name):
        try:
            self.cursor.execute(
                "INSERT INTO subjects(name) VALUES(?)",
                (name,)
            )
            self.conn.commit()
        except:
            pass
        

    def add (self, date, subject, time):
        self.cursor.execute(
            "INSERT INTO study (date, subject, time) VALUES(?, ?, ?)",
            (date, subject, time)
        )
        self.conn.commit()

    def get_all(self):
        self.cursor.execute(
            "SELECT id, date, subject, time FROM study ORDER BY date DESC"
        )
        return self.cursor.fetchall()
    
    def get_by_date(self,date):
        self.cursor.execute(
            "SELECT SUM (time) FROM study WHERE date=?",
            (date,)
        )
        return self.cursor.fetchone()[0]
    
    def get_monthly(self):
        self.cursor.execute("""
           SELECT substr (date,1,7) AS month, SUM(time)
           FROM study
           GROUP BY month
           ORDER BY month
        """)
        rows = self.cursor.fetchall()
        print("月別取得結果：",rows)
        return rows
        
    def get_by_subject(self):
        self.cursor.execute("""
           SELECT subject, SUM(time)
           FROM study
           GROUP BY subject
           ORDER BY SUM(time) DESC
        """)
        return self.cursor.fetchall()
    
    def get_subject_ranking(self):

        self.cursor.execute("""
            SELECT subject, SUM(time) as total_time
            FROM study
            GROUP BY subject
            ORDER BY total_time DESC
            """)
        
        return self.cursor.fetchall()
    
    def delete(self, record_id):
        self.cursor.execute("DELETE FROM study WHERE id = ?", (record_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_dates(self):
        self.cursor.execute(
            "SELECT DISTINCT date FROM study ORDER BY date"
        )
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_study_dates(self):
        self.cursor.execute(
            "SELECT DISTINCT date FROM study"
        )
        return[row[0] for row in self.cursor.fetchall()]

#   アプリ本体

class Study_App:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.db = DBManager()

        self.app = ctk.CTk()
        self.app.title (WINDOW_TITLE)
        self.app.geometry("500x800")

        self.create_ui()
        self.update_history()
        self.update_total_time()
        self.color_calendar()

        self.app.protocol("WM_DELETE_WINDOW", self.on_close)

    def calculate_streak(self):

        dates = self.db.get_dates()

        if not dates:
            return 0
        
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]

        streak = 1
        max_streak = 1

        for i in range(1, len(dates)):

            diff = (dates[i] - dates[i-1]).days

            if diff == 1:
                streak += 1
                max_streak = max(max_streak, streak)

            else:
                streak = 1

        return max_streak
    
    def color_calendar(self):

        dates = self.db.get_study_dates()

        for d in dates:
            date_obj = datetime.strptime(d, "%Y-%m-%d")

            self.date_entry.calevent_create(
               date_obj,
               "study",
               "study_day"
            )

        self.date_entry.tag_config(
            "study_day",
            background = "green",
            foreground="white"
        )
    
    def create_ui(self):
        self.subjects = self.db.get_subjects()

        if not self.subjects:
            self.subjects = ["Python", "SQL", "アルゴリズム", "英語"]

        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand = True, padx = 10, pady=10)

        self.tab_record = self.tabview.add("記録")
        self.tab_graph = self.tabview.add("グラフ")

        #科目追加UI
        ctk.CTkLabel(self.tab_record,text="科目追加").pack()

        self.new_subject_entry = ctk.CTkEntry(self.tab_record)
        self.new_subject_entry.pack(pady=5)

        ctk.CTkButton(
            self.tab_record,
            text="科目追加",
            command=self.add_subject
        ).pack(pady=5)    

        #---入力---
        ctk.CTkLabel(self.tab_record, text="日付").pack()

        self.date_entry = Calendar(
            self.tab_record,
            date_pattern="yyyy-mm-dd"
        )
        
        self.date_entry.pack()

        self.subject_box = ctk.CTkComboBox(
            self.tab_record,
            values = self.subjects
        )
        self.subject_box.pack(pady=5)

        self.subject_box.set("科目を選択")

        ctk.CTkLabel(self.tab_record, text="勉強時間(分)").pack()
        self.time_entry = ctk.CTkEntry(self.tab_record)
        self.time_entry.pack()

        ctk.CTkLabel(self.tab_record, text="今日の目標（分）").pack()
        self.goal_entry = ctk.CTkEntry(self.tab_record)
        self.goal_entry.insert(0,"100")
        self.goal_entry.pack()

        self.total_all_label = ctk.CTkLabel(self.tab_record, text="総学習時間：0分")
        self.total_all_label.pack(pady=5)

        self.total_label = ctk.CTkLabel(self.tab_record, text="")
        self.total_label.pack()

        self.diff_label = ctk.CTkLabel(self.tab_record, text="")
        self.diff_label.pack()

        ctk.CTkButton(self.tab_record, text = "保存", command=self.save).pack(pady=10)
        ctk.CTkButton(self.tab_record, text = "選択削除", command=self.delete).pack()

        self.export_button = ctk.CTkButton(
            self.tab_record,
            text = "csvエクスポート",
            command=self.export_csv
        )

        self.export_button.pack(pady=10)

        ctk.CTkButton(self.tab_record,text="csvインポート",
                      command = self.import_csv).pack()

        #履歴
        history_frame = ctk.CTkFrame(self.tab_record)
        history_frame.pack(fill="both", expand=True, pady=10)

        self.history_table = ttk.Treeview(
            history_frame,
            columns=("id","date","subject","time"),
            show="headings"
        )

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_table.yview)
        self.history_table.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.history_table.pack(side="left", fill="both", expand=True)

        style = ttk.Style()

        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            font=("MS Gothic", 14),
            rowheight=32
        )

        style.configure(
            "Treeview.Heading",
            background="#1f6aa5",
            foreground = "white",
            font=("MS Gothic", 16),
            rowheight=36
        )

        style.map(
            "Treeview",
            background=[("selected", "#1f6aa5")]
        )

        self.history_table.column("id", width=50, anchor="center")
        self.history_table.column("date", width=130, anchor="center")
        self.history_table.column("subject", width=140, anchor="center")
        self.history_table.column("time", width=80, anchor="center")

        self.history_table.heading("id", text = "ID")
        self.history_table.heading("date", text="日付")
        self.history_table.heading("subject", text="科目")
        self.history_table.heading("time", text = "時間(分)")

        self.history_table.tag_configure("even", background="#f2f2f2")
        self.history_table.tag_configure("odd", background="white")


        #グラフ
        ctk.CTkButton(self.tab_graph, text="日別グラフ", command=self.show_daily).pack(pady=5)
        ctk.CTkButton(self.tab_graph, text = "月別グラフ", command=self.show_monthly).pack(pady=5)
        ctk.CTkButton(self.tab_graph, text="科目別グラフ",command=self.show_subject).pack(pady=5)
        ctk.CTkButton(self.tab_graph, text="科目ランキング", command=self.show_ranking).pack(pady=5)

        weekly_button = ctk.CTkButton(
            self.tab_graph,
            text="週間グラフ",
            command=self.weekly_graph
        )
        
        weekly_button.pack(pady=10)
        
        self.streak_label = ctk.CTkLabel(self.tab_record, text="")
        self.streak_label.pack()

     #保存
    def save(self):
        print("saveが呼ばれた")
        date = self.date_entry.get()
        subject = self.subject_box.get().strip()
        time = self.time_entry.get().strip()
        
        print("入力値:", date,subject,time)

        if subject == "科目を選択":
            messagebox.showerror("エラー","科目を選択してください。")
            return
        
        if not time.isdigit() or int(time) <= 0:
             messagebox.showerror("エラー","正しい時間を入力してください")
             return
        
        print("DBに保存する値:", date,subject,int(time))
        self.db.add(date,subject,int(time))

        self.time_entry.delete(0,"end")

        self.update_history()
        self.update_total()
        self.update_total_time()
        self.color_calendar()

    #科目追加
    def add_subject(self):

        new_subject = self.new_subject_entry.get().strip()

        if not new_subject:
            messagebox.showerror("エラー","科目名を入力してください。")
            return
        
        if new_subject in self.subjects:
            messagebox.showwarning("注意","すでに存在します")
            return
        
        self.db.add_subject(new_subject)
        self.subjects = self.db.get_subjects()
        self.subject_box.configure(values = self.subjects)

        self.subject_box.configure(values=self.subjects)

        self.new_subject_entry.delete(0,"end")

        messagebox.showinfo("成功", "科目を追加しました。")

    #CSVエクスポート
    def export_csv(self):

        file_path = filedialog.asksaveasfilename(
            defaultextension = ".csv",
            filetypes = [("csvファイル","*.csv")],
            title="保存先を選択"
        )

        if not file_path:
            return
        
        rows = self.db.cursor.execute(
            "SELECT date, subject, time FROM study"
        ).fetchall()

        with open (file_path, "w", newline="",
                   encoding = "utf-8-sig") as f:
            
            writer = csv.writer(f)
            writer.writerow(["日付","科目","時間(分)"])

            for row in rows:
                writer.writerow(row)

        messagebox.showinfo("完了","csvを書きだしました")
    
    #csvエクスポート
    def import_csv(self):

        file = filedialog.askopenfilename(
            title = "csvファイルを選択",
            filetypes = [("csv files","*.csv")]
        )
        
        if not file:
            return
        
        conn = sqlite3.connect("study.db")
        cur = conn.cursor()

        with open(file, newline="",encoding="UTF-8") as f:
            reader = csv.reader(f)

            next(reader) #ヘッダーをスキップ

            for row in reader:
               date, subject,time = row
               cur.execute(
                   "INSERT INTO study(date,subject,time) VALUES(?,?,?)",
                   (date,subject,int(time))
                )
        conn.commit()
        conn.close()

        messagebox.showinfo("完了","csvをインポートしました。")

        self.update_history()
        self.update_total_time()

     #履歴更新
    def update_history(self):
        
        for row in self.history_table.get_children():
            self.history_table.delete(row)
        
        self.records = self.db.get_all()

        for i, record in enumerate(self.records):
            tag = "even" if i % 2 == 0 else "odd"

            self.history_table.insert(
                "",
                "end",
                values = (record[0], record[1], record[2], record[3]),
                tags = (tag,)
            )

    #削除(IDベース)
    def delete(self):
         
         selected = self.history_table.selection()

         if not selected:
             messagebox.showwarning("注意", "削除行を選択してください。")
             return
         
         record = self.history_table.item(selected[0])
         record_id = record["values"][0]

         if messagebox.askyesno("確認","削除しますか？"):
             self.db.delete(record_id)
             self.update_history()
             self.update_total()

    #合計更新
    def update_total(self):
        date = self.date_entry.get()
        goal = self.goal_entry.get()

        total = self.db.get_by_date(date) or 0
        self.total_label.configure(text=f"今日の合計:{total}分")

        if goal.isdigit():
            diff = int(goal) - total
            if diff > 0:
                self.diff_label.configure(text = f"あと{diff}分")
            else:
                self.diff_label.configure(text="目標達成！")
        else:
            self.diff_label.configure(text="目標は数字で入力")

        streak = self.calculate_streak()
        self.streak_label.configure(text=f"🔥連続学習日数:{streak}日")


    def update_total_time(self):

        conn = sqlite3.connect("study.db")
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(time) FROM study")

        total=cursor.fetchone()[0] or 0

        conn.close()

        self.total_all_label.configure(text=f"総学習時間:{total}分")

     # グラフ
    def show_daily(self):
       date=self.date_entry.get()
       total=self.db.get_by_date(date)

       if not total:
            messagebox.showinfo("情報", "データなし")
            return
       self.plot_bar([date],[total],"日別学習時間", "日付")

    def show_monthly(self):
       rows = self.db.get_monthly()
       print("rowsの中身:", rows)
       if not rows:
          messagebox.showinfo("情報","データなし")
          return

       months = [r[0] for r in rows]
       totals = [r[1] for r in rows]
       self.plot_bar(months, totals, "月別学習時間", "月")

    def show_subject(self):
       rows = self.db.get_by_subject()
       if not rows:
           messagebox.showinfo("情報","データなし")
           return

       subjects = [r[0] for r in rows] 
       totals = [r[1] for r in rows]
       self.plot_bar(subjects, totals, "科目別学習時間","科目")

    def show_ranking(self):

        rows = self.db.get_subject_ranking()

        if not rows:
            messagebox.showinfo("情報","データなし")
            return
        
        text = "科目ランキング\n\n"

        for i, (subject,time) in enumerate(rows, start=1):
            text += f"{i}位{subject}:{time}分\n"

        messagebox.showinfo("科目ランキング",text)
        

    def plot_bar(self, labels, values, title, xlabel):
        plt.figure()
        plt.bar(labels,values)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel("時間(分)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.grid(axis="y")
        plt.show()

    def weekly_graph(self):
        conn = sqlite3.connect("study.db")
        cur = conn.cursor()

        cur.execute("""
        SELECT date, SUM(time)
        FROM study
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
        """)

        data = cur.fetchall()
        conn.close()

        data.reverse()

        dates = []
        times = []

        week = ["月","火","水","木","金","土","日"]

        for row in data:
            d = datetime.strptime(row[0], "%Y-%m-%d")
            dates.append(week[d.weekday()])
            times.append(row[1])


        plt.figure(figsize = (8,4))
        plt.bar(dates,times)

        plt.title("週間学習時間")
        plt.xlabel("日付")
        plt.ylabel("時間(分)")

        plt.show()
        
    def on_close(self):
        self.db.close()
        self.app.destroy()

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = Study_App()
    app.run() 
