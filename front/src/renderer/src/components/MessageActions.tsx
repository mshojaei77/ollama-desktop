import { MessageActionProps } from '../fetch/types'

export const MessageActions = ({ message, onCopy, onRefresh }: MessageActionProps): JSX.Element => {
  return (
    <div className="flex items-center gap-2 mt-1">
      <button
        onClick={() => onCopy(message.content)}
        className="p-1 text-gray-500 hover:text-gray-700"
        title="Copy to clipboard"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
      <button
        onClick={() => onRefresh(message.id)}
        className="p-1 text-gray-500 hover:text-gray-700"
        title="Regenerate response"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"></path>
        </svg>
      </button>
    </div>
  )
}
