import { MCPServer } from '@renderer/fetch/types'

const ServersTable = ({
  serverName,
  serverConfig
}: {
  serverName: string
  serverConfig: MCPServer
}): JSX.Element => {
  return (
    <div key={serverName} className="rounded-lg overflow-hidden border border-gray-300">
      <div className="flex items-center px-6 py-4">
        <div className={`h-3 w-3 rounded-full bg-green-500 mr-3`}></div>
        <h2 className="text-2xl font-bold">{serverName}</h2>
        <span className="ml-4 bg-gray-400 px-3 py-1 rounded-md text-sm">
          {serverConfig.type || 'stdio'}
        </span>
      </div>

      <div className="px-6 py-4 border-t border-gray-300">
        <div className="flex items-center mb-3">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 mr-2 text-gray-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947z"
              clipRule="evenodd"
            />
            <path d="M10 13a3 3 0 100-6 3 3 0 000 6z" />
          </svg>
          <span className="text-gray-400 mr-2">Tools:</span>
          <div className="flex flex-wrap gap-2">
            {serverConfig.tools ? (
              Array.isArray(serverConfig.tools) ? (
                serverConfig.tools.map((tool: string, index: number) => (
                  <span key={index} className="bg-gray-400 px-3 py-1 rounded-md text-sm">
                    {tool}
                  </span>
                ))
              ) : (
                <span className="bg-gray-400 px-3 py-1 rounded-md text-sm">
                  {typeof serverConfig.tools === 'string'
                    ? serverConfig.tools
                    : 'sequentialthinking'}
                </span>
              )
            ) : (
              <span className="bg-gray-400 px-3 py-1 rounded-md text-sm">
                {serverName === 'sequential'
                  ? 'sequentialthinking'
                  : serverName === 'web research'
                    ? 'search_google visit_page take_screenshot'
                    : 'unknown'}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 mr-2 text-gray-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-gray-400 mr-2">Command:</span>
          <code className="bg-gray-400 px-2 py-0.5 rounded-md text-sm font-mono overflow-x-auto max-w-lg">
            {serverConfig.command ||
              (serverName === 'sequential'
                ? 'npx -y @modelcontextprotocol/server-sequential-thinking'
                : serverName === 'web research'
                  ? 'npx -y @mzxrai/mcp-webresearch@latest'
                  : 'unknown command')}
          </code>
        </div>
      </div>
    </div>
  )
}

export default ServersTable
