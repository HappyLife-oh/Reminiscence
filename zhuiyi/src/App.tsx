import { useState, useRef, useEffect } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface Character {
  id: string;
  name: string;
  total_messages: number;
  created_at: string;
}

const API_BASE = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [provider, setProvider] = useState<string>("mimo");
  const [availableProviders, setAvailableProviders] = useState<
    { key: string; name: string; model: string }[]
  >([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [importMode, setImportMode] = useState<"file" | "paste">("file");
  const [importName, setImportName] = useState("");
  const [importContent, setImportContent] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 获取可用的API服务商
  useEffect(() => {
    fetch(`${API_BASE}/api/chat/providers`)
      .then((res) => res.json())
      .then((data) => {
        setAvailableProviders(data);
        if (data.length > 0) {
          setProvider(data[0].key);
        }
      })
      .catch((err) => console.error("获取服务商列表失败:", err));
  }, []);

  // 获取人物列表
  const fetchCharacters = () => {
    fetch(`${API_BASE}/api/data/characters`)
      .then((res) => res.json())
      .then((data) => setCharacters(data))
      .catch((err) => console.error("获取人物列表失败:", err));
  };

  useEffect(() => {
    fetchCharacters();
  }, []);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputValue("");
    setIsLoading(true);

    // 创建一个空的assistant消息用于流式填充
    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await fetch(`${API_BASE}/api/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updatedMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
          provider: provider,
          character_id: selectedCharacter,
          stream: true,
          temperature: 0.8,
          max_tokens: 2000,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const lines = text.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim();
              if (data === "[DONE]") break;

              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  fullContent += parsed.content;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, content: fullContent }
                        : m
                    )
                  );
                }
                if (parsed.error) {
                  // 后端返回错误信息
                  break;
                }
              } catch {
                // 忽略解析错误
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("发送消息失败:", error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: `⚠️ 连接后端失败，请确保后端服务已启动。\n错误: ${error}`,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleImport = async () => {
    if (!importName.trim()) {
      alert("请输入人物名称");
      return;
    }

    setIsImporting(true);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append("character_name", importName);
      formData.append("platform", "manual");

      if (importMode === "file" && importFile) {
        formData.append("file", importFile);
        formData.append("file_type", "auto");
      } else if (importMode === "paste" && importContent) {
        formData.append("content", importContent);
        formData.append("file_type", "txt");
      } else {
        alert("请选择文件或粘贴文本");
        setIsImporting(false);
        return;
      }

      const endpoint = importMode === "file" ? "/api/data/import/file" : "/api/data/import/text";
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      if (response.ok) {
        setImportResult(result);
        fetchCharacters();
        setSelectedCharacter(result.character_id);
        setShowImport(false);
        setMessages([]);
      } else {
        alert(`导入失败: ${result.detail || "未知错误"}`);
      }
    } catch (error) {
      alert(`导入失败: ${error}`);
    } finally {
      setIsImporting(false);
    }
  };

  const selectCharacter = (characterId: string | null) => {
    setSelectedCharacter(characterId);
    setMessages([]);
  };

  const selectedChar = characters.find((c) => c.id === selectedCharacter);

  return (
    <div className="app">
      {/* 侧边栏 */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="app-title">追忆</h1>
          <p className="app-subtitle">此情可待成追忆</p>
        </div>
        <div className="sidebar-content">
          <button className="new-chat-btn" onClick={() => setShowImport(true)}>
            <span>+</span> 导入数据
          </button>

          {/* 人物列表 */}
          <div className="character-list">
            <p className="history-label">人物列表</p>
            <div
              className={`character-item ${selectedCharacter === null ? "active" : ""}`}
              onClick={() => selectCharacter(null)}
            >
              <span className="char-icon">💬</span>
              <div className="char-info">
                <span className="char-name">默认对话</span>
                <span className="char-count">无角色设定</span>
              </div>
            </div>
            {characters.map((char) => (
              <div
                key={char.id}
                className={`character-item ${selectedCharacter === char.id ? "active" : ""}`}
                onClick={() => selectCharacter(char.id)}
              >
                <span className="char-icon">💫</span>
                <div className="char-info">
                  <span className="char-name">{char.name}</span>
                  <span className="char-count">{char.total_messages} 条消息</span>
                </div>
              </div>
            ))}
          </div>

          {/* API服务商选择 */}
          {availableProviders.length > 0 && (
            <div className="provider-selector">
              <p className="history-label">AI 服务商</p>
              <select
                className="provider-select"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
              >
                {availableProviders.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.name} ({p.model})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        <div className="sidebar-footer">
          <button className="settings-btn">⚙️ 设置</button>
        </div>
      </aside>

      {/* 主聊天区域 */}
      <main className="chat-container">
        {/* 当前人物信息 */}
        {selectedChar && (
          <div className="character-banner">
            <span className="banner-icon">💫</span>
            <span className="banner-name">正在与 {selectedChar.name} 对话</span>
            <span className="banner-count">基于 {selectedChar.total_messages} 条消息学习</span>
          </div>
        )}

        {/* 消息列表 */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">💫</div>
              <h2>{selectedChar ? `与 ${selectedChar.name} 对话` : "欢迎使用追忆"}</h2>
              <p>{selectedChar ? `${selectedChar.name} 的数字分身已准备就绪` : "此情可待成追忆，只是当时已惘然"}</p>
              {!selectedChar && (
                <div className="welcome-hints">
                  <div className="hint-card" onClick={() => setShowImport(true)}>
                    <span>📝</span>
                    <p>导入聊天记录</p>
                  </div>
                  <div className="hint-card" onClick={() => setShowImport(true)}>
                    <span>🎤</span>
                    <p>上传语音文件</p>
                  </div>
                  <div className="hint-card" onClick={() => setShowImport(true)}>
                    <span>📸</span>
                    <p>添加照片</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`message ${msg.role === "user" ? "message-user" : "message-assistant"}`}
              >
                <div className="message-avatar">
                  {msg.role === "user" ? "👤" : "💫"}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {msg.content || (
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    )}
                  </div>
                  <div className="message-time">
                    {msg.timestamp.toLocaleTimeString("zh-CN", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              className="message-input"
              placeholder={selectedChar ? `对 ${selectedChar.name} 说...` : "输入消息..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
            >
              ➤
            </button>
          </div>
          <p className="input-hint">
            {selectedChar
              ? `${selectedChar.name} 的数字分身正在学习中`
              : "追忆正在学习中，回复可能不完全准确"}
          </p>
        </div>
      </main>

      {/* 导入数据弹窗 */}
      {showImport && (
        <div className="modal-overlay" onClick={() => setShowImport(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>导入数据</h2>
              <button className="modal-close" onClick={() => setShowImport(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>人物名称</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="输入要创建的人物名称"
                  value={importName}
                  onChange={(e) => setImportName(e.target.value)}
                />
              </div>

              <div className="import-tabs">
                <button
                  className={`tab-btn ${importMode === "file" ? "active" : ""}`}
                  onClick={() => setImportMode("file")}
                >
                  📁 上传文件
                </button>
                <button
                  className={`tab-btn ${importMode === "paste" ? "active" : ""}`}
                  onClick={() => setImportMode("paste")}
                >
                  📋 粘贴文本
                </button>
              </div>

              {importMode === "file" ? (
                <div className="file-upload">
                  <input
                    type="file"
                    ref={fileInputRef}
                    accept=".txt,.csv,.json,.log"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    style={{ display: "none" }}
                  />
                  <div
                    className="upload-area"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {importFile ? (
                      <div className="file-info">
                        <span>📄</span>
                        <p>{importFile.name}</p>
                        <p className="file-size">
                          {(importFile.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    ) : (
                      <>
                        <span className="upload-icon">📁</span>
                        <p>点击选择文件</p>
                        <p className="upload-hint">支持 TXT、CSV、JSON 格式</p>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="paste-area">
                  <textarea
                    className="paste-input"
                    placeholder={`粘贴聊天记录，格式示例：\n2024-01-01 12:00 小明: 你好\n2024-01-01 12:01 小红: 你好啊`}
                    value={importContent}
                    onChange={(e) => setImportContent(e.target.value)}
                    rows={8}
                  />
                </div>
              )}

              {importResult && (
                <div className="import-result">
                  <p>✅ 导入成功！</p>
                  <p>解析了 {importResult.message_count} 条消息</p>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-cancel" onClick={() => setShowImport(false)}>
                取消
              </button>
              <button
                className="btn-import"
                onClick={handleImport}
                disabled={isImporting}
              >
                {isImporting ? "导入中..." : "开始导入"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
