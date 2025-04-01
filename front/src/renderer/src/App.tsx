import Chat from './containers/Chat'
import Sidebar from './containers/Sidebar'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './fetch/queries'

function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1">
          <Chat />
        </div>
      </div>
    </QueryClientProvider>
  )
}

export default App
