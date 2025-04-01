import React, { useState } from 'react'
import SearchSection from './sidebar/SearchSection'
import LogoSection from './sidebar/LogoSection'
import NewChatButton from './sidebar/NewChatButton'
import AvailableChats from './sidebar/AvailableChats'
import FooterSection from './sidebar/FooterSection'

const Sidebar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('')

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setSearchQuery(e.target.value)
  }

  return (
    <div className="flex flex-col h-screen w-64 bg-white border-r border-gray-200">
      <LogoSection />
      <SearchSection searchQuery={searchQuery} handleSearchChange={handleSearchChange} />
      <NewChatButton />
      <AvailableChats searchQuery={searchQuery} />
      <FooterSection />
    </div>
  )
}

export default Sidebar
