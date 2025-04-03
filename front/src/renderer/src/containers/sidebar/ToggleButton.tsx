import { ChevronLeft, PanelsLeftBottom } from 'lucide-react'

const ToggleButton = ({
  isCollapsed,
  setIsCollapsed
}: {
  isCollapsed: boolean
  setIsCollapsed: (isCollapsed: boolean) => void
}): JSX.Element => {
  const toggleSidebar = (): void => {
    setIsCollapsed(!isCollapsed)
  }
  return (
    <button
      onClick={toggleSidebar}
      className={`absolute ${isCollapsed ? '-right-12' : '-right-4'} top-4 bg-white border border-gray-200 rounded-xl p-1 shadow-md z-10`}
      aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
    >
      {isCollapsed ? (
        <PanelsLeftBottom className="h-5 w-5 text-gray-500" />
      ) : (
        <ChevronLeft className="h-5 w-5 text-gray-500" />
      )}
    </button>
  )
}

export default ToggleButton
