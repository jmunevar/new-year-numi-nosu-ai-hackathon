import './styles.css';
import { h } from 'preact';
import { useState } from 'preact/hooks';
import axios from 'axios';
import Message from './message';

const App = () => {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<{ name: string; text: string }[]>([]);

  // Handle the input change
  const handleInputChange = (e: Event) => {
    const target = e.target as HTMLInputElement;
    setInputText(target.value);
  };

  // Handle form submission (sending the input text to the backend)
  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    if (inputText.trim() !== '') {
      try {
        setMessages((prevMessages) => [
          ...prevMessages,
          { name: 'user', text: inputText }
        ]);
        const response = await axios.post('http://localhost:8000/message', { text: inputText });
        const newMessage = response.data.message;

        // Add the new message to the list (could be user or backend response)
        setMessages((prevMessages) => [
          ...prevMessages,
          { name: 'backend', text: newMessage },
        ]);

        setInputText('');  // Clear the input field after submission
      } catch (error) {
        console.error('Error calling the backend:', error);
      }
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Friendly Music AI</h1>
      <div class='chat'>
        {messages.map((message, index) => (
          <Message key={index} name={message.name} text={message.text} />
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputText}
          onInput={handleInputChange}
          placeholder="Type your message..."
        />
        <button type="submit">
          Send
        </button>
      </form>
    </div>
  );
};

export default App;