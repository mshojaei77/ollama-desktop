import ollamaLogo from '../../assets/ollama.png'
import { useNavigate } from 'react-router-dom'
import { Routes } from '../../lib/routes'

const LogoSection = (): JSX.Element => {
  const navigate = useNavigate()

  return (
    <div className="p-4 flex items-center">
      <div
        className="font-bold text-xl flex items-center cursor-pointer"
        onClick={() => navigate(Routes.HOME)}
      >
        <img src={ollamaLogo} alt="Ollama Logo" className="w-6 h-6 mr-1" />
        ollama desktop
      </div>
    </div>
  )
}

export default LogoSection
