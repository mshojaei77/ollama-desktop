import { Input } from '@renderer/components/ui/input'
import { Search } from 'lucide-react'

const SearchSection = ({
  searchQuery,
  setSearchQuery
}: {
  searchQuery: string
  setSearchQuery: (searchQuery: string) => void
}): JSX.Element => {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setSearchQuery(e.target.value)
  }

  return (
    <div className="px-4 mb-2">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
        <Input
          type="text"
          placeholder="Search chats"
          className="pl-8 bg-gray-100 border-0 h-9"
          value={searchQuery}
          onChange={handleSearchChange}
        />
      </div>
    </div>
  )
}

export default SearchSection
