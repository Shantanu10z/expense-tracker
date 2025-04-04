import sys
import os
import json
import calendar
import db
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFileDialog
)
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from datetime import datetime
from functools import partial
import csv
from fpdf import FPDF

ICON_PATH = "icons"
CONFIG_PATH = "config.json"

def load_icon(filename):
    path = os.path.join(ICON_PATH, filename)
    return QIcon(path) if os.path.exists(path) else QIcon()

def get_currency():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f).get("currency", "INR (₹)")
        except:
            pass
    return "INR (₹)"

def save_currency(curr_text):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({"currency": curr_text}, f)
    except:
        pass

class ExpenseTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense Tracker")
        self.setWindowIcon(load_icon("app.png"))
        self.showMaximized()

        self.current_currency = get_currency()
        self.currency_symbol = self.current_currency.split()[-1].strip("()")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.build_form()
        self.build_controls()
        self.build_table()
        self.build_summary()
        self.populate_years()
        self.populate_months()
        self.refresh_table()

    def build_form(self):
        font_label = QFont()
        font_label.setBold(True)

        self.date_input = QLineEdit(datetime.today().strftime("%Y-%m-%d"))
        self.date_input.setMaximumWidth(110)

        self.amount_input = QLineEdit()
        self.amount_input.setMaximumWidth(100)

        self.category_input = QComboBox()
        self.category_input.addItems(["Food", "Travel", "Bills", "Misc", "Savings"])
        self.category_input.setMaximumWidth(100)

        self.desc_input = QLineEdit()
        self.desc_input.setMinimumWidth(200)

        self.add_btn = QPushButton("Add Expense")
        self.add_btn.setIcon(load_icon("add.png"))
        self.add_btn.setMinimumWidth(120)
        self.add_btn.clicked.connect(self.add_expense)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)
        form_layout.addWidget(QLabel("Date:", font=font_label))
        form_layout.addWidget(self.date_input)
        form_layout.addWidget(QLabel("Amount:", font=font_label))
        form_layout.addWidget(self.amount_input)
        form_layout.addWidget(QLabel("Category:", font=font_label))
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(QLabel("Description:", font=font_label))
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(self.add_btn)
        self.layout.addLayout(form_layout)

    def build_controls(self):
        self.year_filter = QComboBox()
        self.month_filter = QComboBox()

        self.category_type_filter = QComboBox()
        self.category_type_filter.addItems([
            "All (Category)", "Food", "Misc", "Travel", "Expense", "Savings"
        ])

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setIcon(load_icon("filter.png"))
        self.filter_btn.clicked.connect(self.refresh_table)

        self.chart_btn = QPushButton("Expense Analysis")
        self.chart_btn.setIcon(load_icon("chart.png"))
        self.chart_btn.clicked.connect(self.show_chart)

        self.savings_btn = QPushButton("Savings Analysis")
        self.savings_btn.setIcon(load_icon("savings.png"))
        self.savings_btn.clicked.connect(self.show_savings_chart)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        control_layout.addWidget(self.year_filter)
        control_layout.addWidget(self.month_filter)
        control_layout.addWidget(self.category_type_filter)
        control_layout.addWidget(self.filter_btn)
        control_layout.addWidget(self.chart_btn)
        control_layout.addWidget(self.savings_btn)
        self.layout.addLayout(control_layout)
    def build_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Amount", "Category", "Description", "Delete"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(
            "QHeaderView::section { background-color: #2c3e50; color: white; font-weight: bold; }"
        )
        self.layout.addWidget(self.table)

    def build_summary(self):
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)

        self.expense_label = QLabel()
        self.savings_label = QLabel()
        self.expense_label.setFont(font)
        self.savings_label.setFont(font)

        self.expense_icon = QLabel()
        self.expense_icon.setPixmap(load_icon("total.png").pixmap(24, 24))
        self.savings_icon = QLabel()
        self.savings_icon.setPixmap(load_icon("savings.png").pixmap(24, 24))

        self.pie_btn = QPushButton("Category Contribution")
        self.pie_btn.setIcon(load_icon("monthwise.png"))
        self.pie_btn.clicked.connect(self.show_category_pie)

        self.vs_btn = QPushButton("Expense vs Savings")
        self.vs_btn.setIcon(load_icon("yearwise.png"))
        self.vs_btn.clicked.connect(self.show_expense_vs_savings_pie)

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setIcon(load_icon("csv.png"))
        self.export_csv_btn.clicked.connect(self.export_to_csv)

        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.setIcon(load_icon("pdf.png"))
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)

        self.currency_box = QComboBox()
        self.currency_box.addItems([
            "INR (₹)", "USD ($)", "EUR (€)", "GBP (£)", "JPY (¥)", "AUD (A$)", "CAD (C$)", "CHF (Fr)", "CNY (¥)",
            "HKD (HK$)", "SGD (S$)", "KRW (₩)", "ZAR (R)", "SEK (kr)", "NZD (NZ$)", "NOK (kr)", "MXN (Mex$)",
            "BRL (R$)", "RUB (₽)", "AED (د.إ)", "THB (฿)", "IDR (Rp)", "TRY (₺)", "PLN (zł)", "DKK (kr)",
            "MYR (RM)", "PHP (₱)", "CZK (Kč)", "HUF (Ft)", "ILS (₪)", "SAR (﷼)", "NGN (₦)", "PKR (₨)",
            "BDT (৳)", "VND (₫)"
        ])
        self.currency_box.setCurrentText(self.current_currency)
        self.currency_box.currentTextChanged.connect(self.change_currency)

        footer = QHBoxLayout()
        footer.addWidget(self.expense_label)
        footer.addWidget(self.expense_icon)
        footer.addSpacing(30)
        footer.addWidget(self.savings_label)
        footer.addWidget(self.savings_icon)
        footer.addStretch()
        footer.addWidget(self.currency_box)
        footer.addStretch()
        footer.addWidget(self.pie_btn)
        footer.addWidget(self.vs_btn)
        footer.addWidget(self.export_csv_btn)
        footer.addWidget(self.export_pdf_btn)
        self.layout.addLayout(footer)

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            headers = ["ID", "Date", "Amount", "Category", "Description"]
            writer.writerow(headers)
            for row in range(self.table.rowCount()):
                writer.writerow([
                    self.table.item(row, 0).text(),
                    self.table.item(row, 1).text(),
                    self.table.item(row, 2).text(),
                    self.table.item(row, 3).text(),
                    self.table.item(row, 4).text()
                ])

        QMessageBox.information(self, "Exported", f"Data exported successfully to:\n{path}")

    def export_to_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Expense Report", 0, 1, "C")
        pdf.ln(5)
        pdf.set_font("Arial", size=10)

        headers = ["ID", "Date", "Amount", "Category", "Description"]
        col_widths = [10, 30, 25, 30, 90]

        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 8, h, border=1)

        pdf.ln()

        for row in range(self.table.rowCount()):
            pdf.cell(col_widths[0], 8, self.table.item(row, 0).text(), border=1)
            pdf.cell(col_widths[1], 8, self.table.item(row, 1).text(), border=1)
            pdf.cell(col_widths[2], 8, self.table.item(row, 2).text(), border=1)
            pdf.cell(col_widths[3], 8, self.table.item(row, 3).text(), border=1)
            pdf.cell(col_widths[4], 8, self.table.item(row, 4).text(), border=1)
            pdf.ln()

        pdf.output(path)
        QMessageBox.information(self, "Exported", f"Data exported successfully to:\n{path}")
    def change_currency(self, text):
        self.current_currency = text
        self.currency_symbol = text.split()[-1].strip("()")
        save_currency(text)
        self.refresh_table()

    def populate_years(self):
        self.year_filter.clear()
        self.year_filter.addItem("All (Year Wise)")
        self.year_filter.addItems(db.get_years())

    def populate_months(self):
        self.month_filter.clear()
        self.month_filter.addItem("All (Months)")
        for i in range(1, 13):
            self.month_filter.addItem(calendar.month_name[i])

    def refresh_table(self):
        self.table.setRowCount(0)
        selected_year = self.year_filter.currentText()
        selected_month = self.month_filter.currentText()
        category_filter = self.category_type_filter.currentText()
        expenses = db.get_expenses(None if selected_year.startswith("All") else selected_year)
        total_expense, total_savings = 0.0, 0.0

        for exp in expenses:
            date_str = exp[1]
            category = exp[3]
            month = calendar.month_name[int(date_str[5:7])]

            if selected_month != "All (Months)" and selected_month != month:
                continue
            if category_filter == "Expense" and category == "Savings":
                continue
            elif category_filter == "Savings" and category != "Savings":
                continue
            elif category_filter not in ["All (Category)", "Expense", "Savings"] and category != category_filter:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(exp):
                self.table.setItem(row, col, QTableWidgetItem(str(val)))
            amount = float(exp[2])
            if category == "Savings":
                total_savings += amount
            else:
                total_expense += amount
            del_btn = QPushButton()
            del_btn.setIcon(load_icon("delete.png"))
            del_btn.setStyleSheet("background-color: white; border: 1px solid red")
            del_btn.setToolTip("Delete")
            del_btn.clicked.connect(partial(self.delete_expense, exp[0]))
            self.table.setCellWidget(row, 5, del_btn)

        self.expense_label.setText(f"Total Expenses: {self.currency_symbol}{total_expense:.2f}")
        self.savings_label.setText(f"Total Savings: {self.currency_symbol}{total_savings:.2f}")

    def add_expense(self):
        date_text = self.date_input.text().strip()
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
            amount = float(self.amount_input.text().strip())
        except:
            QMessageBox.warning(self, "Invalid Input", "Check date and amount format.")
            return
        category = self.category_input.currentText()
        desc = self.desc_input.text().strip()
        db.add_expense(date_text, amount, category, desc)
        self.amount_input.clear()
        self.desc_input.clear()
        self.populate_years()
        self.refresh_table()

    def delete_expense(self, eid):
        db.delete_expense_by_id(eid)
        self.populate_years()
        self.refresh_table()

    def show_chart(self):
        year = self.year_filter.currentText()
        if year.startswith("All"):
            QMessageBox.information(self, "Select Year", "Please select a specific year.")
            return
        data = db.get_monthly_summary(year)
        monthly = {i: 0 for i in range(1, 13)}
        for m, amt in data:
            monthly[int(m)] = amt
        values = [monthly[i] for i in range(1, 13)]
        labels = [f"{calendar.month_abbr[i]}\n({int(values[i - 1])})" for i in range(1, 13)]

        plt.figure(figsize=(10, 5))
        plt.bar(labels, values, color="skyblue")
        plt.title(f"Expenses for {year}", fontsize=13, fontweight='bold')
        plt.xlabel("Month")
        plt.ylabel("Amount")
        plt.tight_layout()
        plt.show(block=False)

    def show_savings_chart(self):
        year = self.year_filter.currentText()
        if year.startswith("All"):
            QMessageBox.information(self, "Select Year", "Please select a specific year.")
            return
        data = [r for r in db.get_expenses(year) if r[3] == "Savings"]
        monthly = {i: 0 for i in range(1, 13)}
        for e in data:
            monthly[int(e[1][5:7])] += float(e[2])
        values = [monthly[i] for i in range(1, 13)]
        labels = [f"{calendar.month_abbr[i]}\n({int(values[i - 1])})" for i in range(1, 13)]

        plt.figure(figsize=(10, 5))
        plt.bar(labels, values, color="lightgreen")
        plt.title(f"Monthly Savings Analysis - {year}", fontsize=13, fontweight='bold')
        plt.xlabel("Month")
        plt.ylabel("Amount Saved")
        plt.tight_layout()
        plt.show(block=False)

    def show_category_pie(self):
        year = self.year_filter.currentText()
        month_filter = self.month_filter.currentText()
        if year.startswith("All"):
            QMessageBox.information(self, "Select Year", "Please select a specific year.")
            return
        data = db.get_expenses(year)
        totals = {}
        for e in data:
            cat = e[3]
            amt = float(e[2])
            mon = calendar.month_name[int(e[1][5:7])]
            if cat == "Savings" or (month_filter != "All (Months)" and month_filter != mon):
                continue
            totals[cat] = totals.get(cat, 0) + amt
        if not totals:
            QMessageBox.information(self, "No Data", "No expense data for this filter.")
            return
        labels, values = list(totals.keys()), list(totals.values())
        explode = [0.05] * len(labels)

        def format_label(pct, vals):
            return f"{pct:.1f}% ({int(pct / 100 * sum(vals))})"

        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.pie(values, labels=labels, autopct=lambda p: format_label(p, values),
               startangle=140, explode=explode, shadow=True,
               textprops=dict(color="black", fontsize=10))
        ax.axis('equal')

        summary = "\n".join([f"{k}: {self.currency_symbol}{v:.2f}" for k, v in totals.items()])
        plt.text(1.6, -0.6, summary, fontsize=10, va='top', ha='left',
                 bbox=dict(boxstyle="round", fc="lightyellow", ec="gray"))
        title = f"Category Contribution - {year}" if month_filter == "All (Months)" else f"{month_filter} {year}"
        plt.title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show(block=False)

    def show_expense_vs_savings_pie(self):
        year = self.year_filter.currentText()
        month = self.month_filter.currentText()

        if year.startswith("All"):
            QMessageBox.information(self, "Select Year", "Please select a specific year.")
            return

        data = db.get_expenses(year)
        total_exp = 0.0
        total_sav = 0.0

        for row in data:
            m = calendar.month_name[int(row[1][5:7])]
            if month != "All (Months)" and m != month:
                continue
            amount = float(row[2])
            if row[3] == "Savings":
                total_sav += amount
            else:
                total_exp += amount

        if total_exp == 0 and total_sav == 0:
            QMessageBox.information(self, "No Data", "No data available for this selection.")
            return

        labels = ["Expenses", "Savings"]
        values = [total_exp, total_sav]
        explode = [0.05, 0.05]

        def format_label(pct, vals):
            return f"{pct:.1f}% ({int(pct / 100 * sum(vals))})"

        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.pie(values, labels=labels, autopct=lambda p: format_label(p, values),
               startangle=90, explode=explode, shadow=True,
               textprops=dict(color="black", fontsize=10))
        ax.axis('equal')

        summary = f"Expenses: {self.currency_symbol}{total_exp:.2f}\nSavings: {self.currency_symbol}{total_sav:.2f}"
        plt.text(1.6, -0.5, summary, fontsize=10, va='top', ha='left',
                 bbox=dict(boxstyle="round", fc="lightyellow", ec="gray"))

        title = f"Expense vs Savings - {year}" if month == "All (Months)" else f"{month} {year}"
        plt.title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show(block=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ExpenseTracker()
    win.show()
    sys.exit(app.exec())
