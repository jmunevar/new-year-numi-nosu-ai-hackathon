import { h } from 'preact';
import { useState } from 'preact/hooks';

const App = () => {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<string[]>([]);

  // Handle input change
  const handleInputChange = (e: Event) => {
    const target = e.target as HTMLInputElement;
    setInputText(target.value);
  };

  // Handle form submission
  const handleSubmit = (e: Event) => {
    e.preventDefault();
    if (inputText.trim()) {
      setMessages([...messages, inputText]);  // Add message to the array
      setInputText('');  // Clear the input field
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Friendly Music AI</h1>
      <div style={{ marginBottom: '20px' }}>
        {messages.map((message, index) => (
          <div key={index} style={{ marginBottom: '10px' }}>
            <strong>You: </strong>{message}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputText}
          onInput={handleInputChange}
          placeholder="Type your message..."
          style={{
            padding: '10px',
            width: '300px',
            marginRight: '10px',
            border: '1px solid #ccc',
            borderRadius: '4px',
          }}
        />
        <button
          type="submit"
          style={{
            padding: '10px 20px',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            borderRadius: '4px',
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default App;