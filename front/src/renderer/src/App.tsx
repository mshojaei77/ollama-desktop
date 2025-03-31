import Sidebar from './containers/Sidebar'
import Chat from './containers/Chat'

function App(): JSX.Element {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-white">
      <Sidebar />
      <div className="flex-1">
        <Chat />
      </div>
    </div>
  )
}

export default App
