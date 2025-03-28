import Versions from './components/Versions'
import electronLogo from './assets/electron.svg'
import { Button } from './components/ui/button'
import Chat from './containers/Chat'
function App(): JSX.Element {
  const ipcHandle = (): void => window.electron.ipcRenderer.send('ping')

  return (
    <div className="container mx-auto p-4 flex flex-col items-center justify-center min-h-screen">
      <Chat />
    </div>
  )
}

export default App
