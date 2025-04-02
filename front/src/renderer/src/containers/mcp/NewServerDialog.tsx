import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '../../components/ui/dialog'
import { Input } from '../../components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../../components/ui/select'
import { Button } from '../../components/ui/button'
import { NewServerForm } from '@renderer/fetch/types'
import { useState } from 'react'

const NewServerDialog = ({
  isDialogOpen,
  setIsDialogOpen
}: {
  isDialogOpen: boolean
  setIsDialogOpen: (isOpen: boolean) => void
}): JSX.Element => {
  const [newServer, setNewServer] = useState<NewServerForm>({
    name: '',
    command: '',
    type: 'command'
  })
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target
    setNewServer((prev) => ({ ...prev, [name]: value }))
  }

  const handleTypeChange = (value: string): void => {
    setNewServer((prev) => ({ ...prev, type: value }))
  }

  const handleAddServer = (): void => {
    console.log('Adding server:', newServer)
    setNewServer({ name: '', command: '', type: 'command' })
    setIsDialogOpen(false)
  }

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogContent className="bg-white text-black">
        <DialogHeader>
          <DialogTitle>Add MCP Server</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <label htmlFor="name" className="text-right font-medium">
              Name
            </label>
            <Input
              id="name"
              name="name"
              value={newServer.name}
              onChange={handleInputChange}
              className="col-span-3 bg-white text-black border-gray-300"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <label htmlFor="type" className="text-right font-medium">
              Type
            </label>
            <Select value={newServer.type} onValueChange={handleTypeChange}>
              <SelectTrigger className="col-span-3 bg-white text-black border-gray-300">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent className="bg-white text-black">
                <SelectItem value="command">command</SelectItem>
                <SelectItem value="stdio">stdio</SelectItem>
                <SelectItem value="http">http</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <label htmlFor="command" className="text-right font-medium">
              Command
            </label>
            <Input
              id="command"
              name="command"
              value={newServer.command}
              onChange={handleInputChange}
              className="col-span-3 bg-white text-black border-gray-300"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            type="submit"
            onClick={handleAddServer}
            className="bg-white text-black border border-gray-300 hover:bg-gray-100"
          >
            Add Server
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default NewServerDialog
