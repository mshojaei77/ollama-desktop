import { useState } from 'react'; // Import useState
import { useChatStore } from '@renderer/store/chatStore';
import { useModels, useModelInfo } from '@renderer/fetch/queries'; // No need for useModelInfo here, ModelDetailsView handles it
import { getIconPath, getModelDisplayName } from '@renderer/utils';
import ModelDetailsView from '@renderer/components/ModelDetailsView'; // Import the new component
import { Info } from 'lucide-react'; // Import an icon for click indication
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose
} from '@renderer/components/ui/dialog'; // Import Dialog components
import { Button } from '@renderer/components/ui/button'; // Import Button
import { Badge } from '@renderer/components/ui/badge'; // Import Badge component if available, or use simple spans

const ChatHeader = () => {
  const selectedModelId = useChatStore((state) => state.selectedModel);
  const { data: modelsResponse } = useModels(); // Fetch all models to find details
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Find the full details of the selected model - used for display name/desc only
  const selectedModelBasicInfo = modelsResponse?.models?.find(model => model.name === selectedModelId);

  const displayName = selectedModelBasicInfo?.name || selectedModelId || 'Unknown Model';
  // Keep description simpler or remove if redundant with dialog
  // const description = selectedModelDetails?.description || (selectedModelId ? `Chatting with ${selectedModelId}` : 'No model selected');
  const iconPath = getIconPath(selectedModelId); // Use the utility function

  // Fetch detailed info for tags and dialog
  const { data: modelDetails } = useModelInfo(selectedModelId);
  const tags = modelDetails?.tags || []; // Get tags, default to empty array

  if (!selectedModelId) {
    return null; // Don't render if no model is selected
  }

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      {/* Header Container - Not the trigger anymore */}
      <div
        className="sticky top-0 z-10 flex items-center px-4 py-3 bg-[hsl(var(--background))] border-b border-[hsl(var(--border))] shadow-sm" // Removed cursor-pointer, hover effect, group, onClick, onKeyDown, role, tabIndex
      >
        {/* Icon Container */}
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-transparent mr-3 flex-shrink-0 ring-1 ring-slate-200/30 dark:ring-slate-700/30"> {/* Transparent frame with subtle border */}
          <img
            src={iconPath}
            alt={`${displayName} icon`}
            className="w-5 h-5 rounded-full object-contain" // Slightly smaller icon
            onError={(e) => {
              e.currentTarget.src = new URL('../assets/models/default.png', import.meta.url).href;
            }}
          />
        </div>
        {/* Model Name and Tags */}
        <div className="flex-grow overflow-hidden mr-2"> {/* Added margin-right */}
          <h2 className="text-base font-medium truncate">{getModelDisplayName(displayName)}</h2>
          {/* Render Tags if they exist */}
          {tags.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1 items-center"> {/* Ensure vertical alignment */}
              {tags.slice(0, 3).map(tag => ( // Limit initially visible tags (example: show first 3)
                <Badge key={tag} variant="secondary" className="text-xs px-1.5 py-0.5 whitespace-nowrap">
                  {tag}
                </Badge>
              ))}
              {tags.length > 3 && ( // Indicate more tags if applicable
                 <span className="text-xs text-muted-foreground ml-1">+{tags.length - 3} more</span>
              )}
            </div>
          )}
        </div>

        {/* Clickable Trigger for Dialog (Info Icon Button) */}
        <DialogTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="flex-shrink-0 h-8 w-8 rounded-full" // Make button dimensions match icon click area intention
            aria-label="View model details"
          >
            <Info className="h-4 w-4 text-muted-foreground" />
          </Button>
        </DialogTrigger>
      </div>

      {/* Render DialogContent only when open */}
      {selectedModelId && (
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Model Details: {getModelDisplayName(selectedModelId)}</DialogTitle>
            <DialogDescription>
              Detailed information retrieved from Ollama.
            </DialogDescription>
          </DialogHeader>
          {/* Use the extracted component */}
          <ModelDetailsView modelName={selectedModelId} />
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="secondary">
                Close
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      )}
    </Dialog>
  );
};

export default ChatHeader; 