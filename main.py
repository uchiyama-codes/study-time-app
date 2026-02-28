import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import messagebox
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3

import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'


class StudyApp:

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.app=ctk.CTk()
        self.app.title("学習記録アプリ")
        self.app.geometry("400x1000")

        #タブ作成
        self.tabview = ctk.CTkTabview(self.app, width=380)
        self.tabview.pack(pady=10, fill="both", expand=True)

        self.tab_record=self.tabview.add("記録")
        self.tab_graph = self.tabview.add("グラフ")

        #データベース作成
        self.conn = sqlite3.connect("study.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS study(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            subject TEXT,
            time INTEGER       
        )
        """)
        self.conn.commit()

        #---日付---
        ctk.CTkLabel(self.tab_record, text="日付").pack(pady=(10,0))
        self.date_entry=DateEntry(self.tab_record,date_pattern="yyyy-mm-dd")
        self.date_entry.pack()

        #--勉強内容--
        ctk.CTkLabel(self.tab_record, text="勉強内容").pack(pady=(10,0))
        self.subject_entry = ctk.CTkEntry(self.tab_record)
        self.subject_entry.pack()

        #--勉強時間--
        ctk.CTkLabel(self.tab_record, text="勉強時間(分)").pack(pady=(10,0))
        self.time_entry=ctk.CTkEntry(self.tab_record)
        self.time_entry.pack()

        #今日の目標
        ctk.CTkLabel(self.tab_record, text="今日の目標（分）").pack(pady=(10,0))
        self.goal_entry=ctk.CTkEntry(self.tab_record)
        self.goal_entry.insert(0,100)
        self.goal_entry.pack()   

        #--合計表示--
        self.total_label = ctk.CTkLabel(self.tab_record, text="今日の合計:0分")
        self.total_label.pack(pady=(10,0))

        self.diff_label= ctk.CTkLabel(self.tab_record, text="")
        self.diff_label.pack()

        #--保存ボタン--
        self.save_button = ctk.CTkButton(self.tab_record, text="保存", command=self.save_data)
        self.save_button.pack(pady=20)

        #--履歴表示--
        ctk.CTkLabel(self.tab_record, text="履歴").pack(pady=(10,0))

        self.history_box = ctk.CTkTextbox(self.tab_record, height = 150)
        self.history_box.pack(padx=10, pady=5, fill="both")

        self.update_total()
        self.update_history()

        #--削除ボタン--
        self.delete_button = ctk.CTkButton(
            self.tab_record,
            text = "選択行を削除",
            command=self.delete_selected
        )
        self.delete_button.pack(pady=5)

        #日別グラフボタン
        self.graph_button = ctk.CTkButton(
            self.tab_graph,
            text = "日別グラフ表示",
            command=self.show_daily_graph
        )
        self.graph_button.pack(pady=5)

        #月別グラフボタン
        self.month_graph_button = ctk.CTkButton(
            self.tab_record,
            text="月別グラフ表示",
            command=self.show_monthly_graph
        )
        self.month_graph_button.pack(pady=5)

        #科目別グラフボタン
        self.subject_graph_button = ctk.CTkButton(
            self.tab_record,
            text = "科目別グラフ表示",
            command=self.show_subject_graph
        )
        self.subject_graph_button.pack(pady=5)

    def show_daily_graph(self):
        today_str = self.date_entry.get()
       
        self.cursor.execute(
            "SELECT SUM(time) FROM study WHERE date = ?",
            (today_str,)
        )
        result= self.cursor.fetchone()

        if result[0] is None:
            messagebox.showinfo("情報", "この日のデータはありません。")
            return
        
        total = result[0]
            
        #グラフ作成
        plt.figure()
        plt.bar([today_str], [total])
        plt.xlabel("日付")
        plt.ylabel("勉強時間(分)")
        plt.title("日別学習時間")
        plt.show()

    def show_monthly_graph(self):

        self.cursor.execute("""
            SELECT substr(date,1,7) AS month, SUM(time)
            FROM study
            GROUP BY month
            ORDER BY month
       """ )
        
        rows = self.cursor.fetchall()
        if not rows:
            messagebox.showinfo("情報","データがありません。")
            return
        
        months = []
        totals = []

        for row in rows:
            months.append(row[0])
            totals.append(row[1])

        #グラフ作成
        plt.figure()
        plt.bar(months,totals)
        plt.xlabel("月")
        plt.ylabel("勉強時間(分)")
        plt.title("月別学習時間")
        plt.xticks(rotation=45)
        plt.show()

    def show_subject_graph(self):

        self.cursor.execute("""
             SELECT subject, SUM(time)
             FROM study
             GROUP BY subject
             ORDER BY SUM(time) DESC
             """)
        
        rows = self.cursor.fetchall()

        if not rows:
            messagebox.showinfo("情報","データがありません。")
            return
        
        subjects = []
        totals = []

        for row in rows:
            subjects.append(row[0])
            totals.append(row[1])

        plt.figure()
        plt.bar(subjects,totals)
        plt.xlabel("科目")
        plt.ylabel("合計勉強時間(分)")
        plt.title("科目別学習期間")
        plt.xticks(rotation=45)
        plt.show() 

    def update_history(self):
        self.history_box.delete("1.0", "end")

        self.cursor.execute(
            "SELECT date, subject, time FROM study ORDER BY date DESC"
        )

        rows = self.cursor.fetchall()
    
        for row in rows:
            self.history_box.insert(
                "end", 
                f"{row[0]} | {row[1]} | {row[2]}分\n"
            )


    def save_data(self):
        date = self.date_entry.get()
        subject=self.subject_entry.get()
        time = self.time_entry.get()

        if not time.isdigit():
            messagebox.showerror("エラー", "勉強時間は数字で入力してください。")
            return
        
        self.cursor.execute(
            "INSERT INTO study (date, subject, time) VALUES(?,?,?)",
            (date, subject, int(time))
        )
        self.conn.commit()

        self.subject_entry.delete(0,"end")
        self.time_entry.delete(0,"end")
        
        messagebox.showinfo("保存完了", "記録を保存しました。")
        self.update_total()
        self.update_history()


    def delete_selected(self):
        try:
            selected_text = self.history_box.get("sel.first", "sel.last")
        except:
            messagebox.showwarning("注意","削除する行を選択してください。")
            return
        
        if not messagebox.askyesno("確認","本当に削除しますか？"):
            return
        
        #表示形式:2026-02-15 | 英語| 60分
        parts = selected_text.strip().split(" | ")
        date = parts[0]
        subject = parts[1]
        time = int(parts[2].replace("分",""))

        self.cursor.execute(
            "DELETE FROM study WHERE date=? AND subject=? AND time=?",
            (date, subject,time)    
        )
        self.conn.commit()

        messagebox.showinfo("完了","削除しました。")
        self.update_total()
        self.update_history()
        
        

    def update_total(self):
       today_str = self.date_entry.get()
       goal=self.goal_entry.get()

       self.cursor.execute(
           "SELECT SUM(time) FROM study WHERE date = ?",
           (today_str,)    
       )
       result = self.cursor.fetchone()

       total = result[0] if result[0] else 0

       self.total_label.configure(text=f"今日の合計:{total}分")

       if goal.isdigit():
           goal = int(goal)
           diff = goal - total
           if diff > 0:
               self.diff_label.configure(text=f"あと{diff}分頑張ろう")
           else:
               self.diff_label.configure(text="目標達成！おめでとう！")
       else:
           self.diff_label.configure(text = "目標は数字で入力してください。")

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = StudyApp()
    app.run()