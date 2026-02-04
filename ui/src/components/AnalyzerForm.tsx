/**
 * AnalyzerForm - input form for email analysis with sample presets
 */

import { useState } from "react";
import type { AnalyzeRequest } from "../api/types";

interface Props {
  onAnalyze: (request: AnalyzeRequest) => void;
  loading?: boolean;
}

// Sample presets for quick demos
const SAMPLES = {
  punycode: {
    subject: "Microsoft Security Update",
    body: "Please sign in to keep your account active: https://xn--pple-43d.com/login",
    from_email: "security@microsoft.com",
    reply_to: "",
  },
  shortener_otp: {
    subject: "דחוף: אימות חשבון נדרש",
    body: `שלום,

החשבון שלך יינעל תוך 24 שעות אם לא תאמת אותו.

לחץ כאן לאימות: https://bit.ly/3xYz123

נא להזין את קוד האימות שנשלח אליך: ____

בברכה,
צוות התמיכה הטכנית`,
    from_email: "support@bank-security.com",
    reply_to: "phisher@gmail.com",
  },
  clean: {
    subject: "Meeting Tomorrow",
    body: `Hi Team,

Just a reminder about our meeting tomorrow at 10am.

Please review the attached agenda.

Best,
John`,
    from_email: "john@company.com",
    reply_to: "",
  },
} as const;

export function AnalyzerForm({ onAnalyze, loading }: Props) {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const [replyTo, setReplyTo] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const request: AnalyzeRequest = {
      subject: subject,
      body: body,
      from_email: fromEmail || null,
      reply_to: replyTo || null,
      headers_raw: "",
      attachments: [],
    };
    
    onAnalyze(request);
  };

  const loadSample = (key: keyof typeof SAMPLES) => {
    const sample = SAMPLES[key];
    setSubject(sample.subject);
    setBody(sample.body);
    setFromEmail(sample.from_email);
    setReplyTo(sample.reply_to);
  };

  const clearForm = () => {
    setSubject("");
    setBody("");
    setFromEmail("");
    setReplyTo("");
  };

  const isValid = subject.trim() || body.trim();

  return (
    <form onSubmit={handleSubmit} className="analyzer-form">
      {/* Sample Presets */}
      <div className="sample-buttons">
        <span className="sample-label">Quick load:</span>
        <button 
          type="button" 
          className="btn btn-sample" 
          onClick={() => loadSample("punycode")}
          title="Punycode domain attack"
        >
          🔗 Punycode
        </button>
        <button 
          type="button" 
          className="btn btn-sample" 
          onClick={() => loadSample("shortener_otp")}
          title="URL shortener + OTP request (Hebrew)"
        >
          🔗 Shortener+OTP
        </button>
        <button 
          type="button" 
          className="btn btn-sample" 
          onClick={() => loadSample("clean")}
          title="Clean benign email"
        >
          ✅ Clean
        </button>
        {isValid && (
          <button 
            type="button" 
            className="btn btn-clear" 
            onClick={clearForm}
            title="Clear all fields"
          >
            🗑️ Clear
          </button>
        )}
      </div>

      {/* Row: From + Reply-To */}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">From Email</label>
          <input
            type="email"
            value={fromEmail}
            onChange={(e) => setFromEmail(e.target.value)}
            placeholder="sender@example.com"
            className="form-input"
          />
        </div>
        <div className="form-group">
          <label className="form-label">Reply-To</label>
          <input
            type="email"
            value={replyTo}
            onChange={(e) => setReplyTo(e.target.value)}
            placeholder="reply@example.com"
            className="form-input"
          />
        </div>
      </div>

      {/* Subject */}
      <div className="form-group">
        <label className="form-label">Subject</label>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Email subject..."
          className="form-input"
        />
      </div>

      {/* Body */}
      <div className="form-group">
        <label className="form-label">Body</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Paste email body here..."
          rows={10}
          className="form-input form-textarea"
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading || !isValid}
        className="btn btn-primary btn-large"
      >
        {loading ? "⏳ Analyzing..." : "🔍 Analyze Email"}
      </button>
    </form>
  );
}
