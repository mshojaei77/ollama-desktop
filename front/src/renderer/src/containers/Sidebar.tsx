import React, { useState } from 'react'
import SearchSection from './sidebar/SearchSection'
import LogoSection from './sidebar/LogoSection'
import NewChatButton from './sidebar/NewChatButton'
import AvailableChats from './sidebar/AvailableChats'
import FooterSection from './sidebar/FooterSection'
import ToggleButton from './sidebar/ToggleButton'

const Sidebar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false)

  return (
    <div
      className={`flex flex-col h-screen bg-white transition-all duration-300 ease-in-out ${isCollapsed ? 'w-0 border-none' : 'w-64 border-r border-gray-200'} relative`}
    >
      <ToggleButton isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
      {!isCollapsed && (
        <>
          <LogoSection />
          <SearchSection searchQuery={searchQuery} setSearchQuery={setSearchQuery} />
          <NewChatButton />
          <div className="flex-1 overflow-y-auto">
            <AvailableChats searchQuery={searchQuery} />
          </div>
          <FooterSection />
        </>
      )}
    </div>
  )
}

export default Sidebar
