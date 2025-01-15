import { h } from 'preact';

interface MessageProps {
  name: 'user' | 'backend';
  text: string;
}

const Message = ({ name, text }: MessageProps) => {
  return (
    <div class={name} style={{ marginBottom: '10px' }}>
      {text}
    </div>
  );
};

export default Message;