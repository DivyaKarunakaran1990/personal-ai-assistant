import { useRef, useState } from "react";
import "./App.css";

type Message = {
  role: "user" | "ai";
  content: string;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "ai",
      content:
        "Hi! I'm your personal AI assistant. I can remember information, manage your shopping list, and help with everyday tasks.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // =========================
  // PDF UPLOAD
  // =========================
  const uploadPdf = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please select a PDF file.");
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        "http://localhost:8000/upload-pdf",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("PDF upload failed");
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: `📄 ${data.filename} has been uploaded successfully.`,
        },
      ]);
    } catch (error) {
      console.error("PDF upload error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content:
            "Sorry, I couldn't upload the PDF. Please check that the backend is running.",
        },
      ]);
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // =========================
  // SEND CHAT MESSAGE
  // =========================
  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: userMessage,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      console.log("Sending to backend:", userMessage);

      const response = await fetch(
        "http://localhost:8000/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: userMessage,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to connect to assistant");
      }

      const data = await response.json();

      console.log("Backend response:", data);

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: data.response,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content:
            "Sorry, I couldn't connect to the assistant. Please make sure the backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // ENTER KEY
  // =========================
  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  };

  // =========================
  // UI
  // =========================
  return (
    <div className="app">

      {/* Hidden PDF file picker */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={uploadPdf}
        style={{ display: "none" }}
      />

      {/* =========================
          SIDEBAR
      ========================= */}
      <aside className="sidebar">

        <div className="logo">
          <div className="logo-icon">🤖</div>

          <div>
            <h2>Personal AI</h2>
            <span>Assistant</span>
          </div>
        </div>

        <nav>

          <button className="nav-item active">
            🏠
            <span>Assistant</span>
          </button>

          <button className="nav-item">
            🧠
            <span>Memory</span>
          </button>

          <button className="nav-item">
            🛒
            <span>Shopping</span>
          </button>

          {/* PDF DOCUMENTS */}
          <button
            className="nav-item"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            📄
            <span>
              {uploading ? "Uploading..." : "Documents"}
            </span>
          </button>

          <button className="nav-item">
            💰
            <span>Bills</span>
          </button>

          <button className="nav-item">
            📅
            <span>Activities</span>
          </button>

          <button className="nav-item">
            ⏰
            <span>Reminders</span>
          </button>

        </nav>

        <div className="sidebar-footer">
          <div className="status-dot"></div>
          <span>AI is running locally</span>
        </div>

      </aside>

      {/* =========================
          MAIN CHAT
      ========================= */}
      <main className="chat-container">

        <header className="chat-header">

          <div>
            <h1>Divya's Personal Assistant</h1>

            <p>
              Ask me to remember, organise or manage
              things for you.
            </p>
          </div>

          <div className="online-status">
            <span></span>
            Local AI
          </div>

        </header>

        {/* =========================
            MESSAGES
        ========================= */}
        <section className="messages">

          {messages.map((message, index) => (

            <div
              key={index}
              className={`message-row ${message.role}`}
            >

              {message.role === "ai" && (
                <div className="avatar ai-avatar">
                  🤖
                </div>
              )}

              <div className="message">
                {message.content}
              </div>

              {message.role === "user" && (
                <div className="avatar user-avatar">
                  D
                </div>
              )}

            </div>

          ))}

          {/* AI typing indicator */}
          {loading && (
            <div className="message-row ai">

              <div className="avatar ai-avatar">
                🤖
              </div>

              <div className="message typing">

                <span></span>
                <span></span>
                <span></span>

              </div>

            </div>
          )}

        </section>

        {/* =========================
            CHAT INPUT
        ========================= */}
        <div className="chat-input-area">

          <div className="suggestions">

            <button
              onClick={() =>
                setInput(
                  "What's on my shopping list?"
                )
              }
            >
              🛒 Shopping list
            </button>

            <button
              onClick={() =>
                setInput(
                  "What do you remember about Nilan?"
                )
              }
            >
              🧠 Ask about memory
            </button>

            <button
              onClick={() =>
                setInput("Remember that ")
              }
            >
              💾 Remember something
            </button>

          </div>

          <div className="input-wrapper">

            <input
              type="text"
              placeholder="Ask your personal assistant..."
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={handleKeyDown}
            />

            <button
              className="send-button"
              onClick={sendMessage}
              disabled={
                loading || !input.trim()
              }
            >
              ➤
            </button>

          </div>

          <p className="privacy-note">
            🔒 Your assistant runs locally on your computer.
          </p>

        </div>

      </main>

    </div>
  );
}

export default App;