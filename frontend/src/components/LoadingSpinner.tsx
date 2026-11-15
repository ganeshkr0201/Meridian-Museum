export default function LoadingSpinner({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-10 h-10 border-4 border-museum-border border-t-museum-accent rounded-full animate-spin" />
      <p className="text-museum-muted text-sm">{message}</p>
    </div>
  )
}
