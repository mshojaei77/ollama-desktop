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
      className={`absolute ${isCollapsed ? 'left-4' : '-right-4'} top-14 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-xl p-1 shadow-md z-20 transition-all duration-300 ease-in-out`}
      aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
    >
      {isCollapsed ? (
        <PanelsLeftBottom className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
      ) : (
        <ChevronLeft className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
      )}
    </button>
  )
}

export default ToggleButton
