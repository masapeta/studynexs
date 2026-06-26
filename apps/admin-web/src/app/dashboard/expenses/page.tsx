"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { AppFileInput } from "@/components/ui/AppFileInput";
import { PageShell } from "@/components/layout/PageShell";
import { inr } from "@/lib/format";
import { Plus, Receipt } from "lucide-react";

const CATEGORIES = ["Supplies", "Utilities", "Maintenance", "Transport", "Other"];

type Expense = {
  id: string;
  vendor: string;
  category: string;
  amount: number;
  expense_date: string;
  receipt_file_id?: string | null;
};

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [monthTotal, setMonthTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    vendor: "",
    category: "Supplies",
    amount: "",
    expense_date: new Date().toISOString().slice(0, 10),
  });
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [receiptId, setReceiptId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api<{ data: { expenses: Expense[]; month_total: number } }>(
        "/api/v1/ops/expenses"
      );
      setExpenses(res.data?.expenses || []);
      setMonthTotal(res.data?.month_total || 0);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load expenses"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function uploadReceipt(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await api<{ data: { id: string } }>("/api/v1/files/upload", {
      method: "POST",
      body: fd,
    });
    setReceiptId(res.data?.id || null);
  }

  async function addExpense() {
    if (!form.vendor.trim() || !form.amount) {
      setError("Vendor and amount are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      if (receiptFile && !receiptId) {
        await uploadReceipt(receiptFile);
      }
      await api("/api/v1/ops/expenses", {
        method: "POST",
        body: JSON.stringify({
          vendor: form.vendor.trim(),
          category: form.category,
          amount: Number(form.amount),
          expense_date: form.expense_date,
          receipt_file_id: receiptId,
        }),
      });
      setForm({
        vendor: "",
        category: "Supplies",
        amount: "",
        expense_date: new Date().toISOString().slice(0, 10),
      });
      setReceiptId(null);
      setReceiptFile(null);
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add expense"));
    } finally {
      setSaving(false);
    }
  }

  function formatDate(iso: string) {
    try {
      return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
    } catch {
      return iso;
    }
  }

  return (
    <PageShell title="Expenses" subtitle={`${inr(monthTotal)} recorded this month`}>
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      <div className="gw-card gw-card-pad gw-expense-form">
        <input
          className="form-input"
          placeholder="Vendor / payee"
          value={form.vendor}
          onChange={(e) => setForm({ ...form, vendor: e.target.value })}
        />
        <AppSelect
          variant="field"
          value={form.category}
          onChange={(v) => setForm({ ...form, category: v })}
          aria-label="Expense category"
          options={CATEGORIES.map((c) => ({ value: c, label: c }))}
        />
        <input
          className="form-input"
          type="number"
          min={1}
          placeholder="₹ Amount"
          value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })}
        />
        <AppFileInput
          variant="compact"
          accept="image/*,.pdf"
          file={receiptFile}
          onChange={setReceiptFile}
          placeholder="Receipt (optional)"
          aria-label="Receipt"
        />
        <button type="button" className="btn btn-primary gw-btn-icon" onClick={addExpense} disabled={saving}>
          <Plus size={18} />
        </button>
      </div>

      <div className="gw-card" style={{ overflow: "hidden" }}>
        {loading ? (
          <div className="gw-center" style={{ padding: 40 }}>
            <div className="spinner" />
          </div>
        ) : expenses.length === 0 ? (
          <p className="gw-muted gw-center" style={{ padding: 40 }}>
            No expenses recorded yet.
          </p>
        ) : (
          <ul className="gw-expense-list">
            {expenses.map((e) => (
              <li key={e.id} className="gw-expense-row">
                <Receipt size={16} className="gw-expense-icon" />
                <div className="gw-expense-main">
                  <div className="gw-expense-vendor">{e.vendor}</div>
                  <div className="gw-expense-meta">
                    {formatDate(e.expense_date)} · {e.category}
                  </div>
                </div>
                <div className="gw-expense-amount">{inr(e.amount)}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </PageShell>
  );
}
