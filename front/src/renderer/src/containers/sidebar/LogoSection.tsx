import ollamaLogo from '../../assets/ollama.png'

const LogoSection = (): JSX.Element => {
  return (
    <div className="p-4 flex items-center">
      <div className="font-bold text-xl flex items-center">
        <img src={ollamaLogo} alt="Ollama Logo" className="w-6 h-6 mr-1" />
        ollama desktop
      </div>
    </div>
  )
}

export default LogoSection
