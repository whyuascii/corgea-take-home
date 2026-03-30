export default function FindingComments({
  comments,
  commentText,
  onCommentTextChange,
  onAddComment,
  onDeleteComment,
  commentLoading,
  currentUsername,
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Comments</h3>
      <div className="space-y-3">
        {comments?.map((c) => (
          <div key={c.id} className="flex gap-2.5 text-xs">
            <div className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-[10px] text-gray-300 font-medium flex-shrink-0">
              {(c.username || '?')[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-gray-200 font-medium">{c.username}</span>
                <span className="text-gray-600">{new Date(c.created_at).toLocaleDateString()}</span>
                {currentUsername === c.username && (
                  <button
                    onClick={() => onDeleteComment(c.id)}
                    className="text-gray-600 hover:text-red-400 ml-auto"
                    title="Delete comment"
                  >
                    &times;
                  </button>
                )}
              </div>
              <p className="text-gray-400 mt-0.5 whitespace-pre-wrap break-words">{c.text}</p>
            </div>
          </div>
        ))}
        {(!comments || comments.length === 0) && (
          <p className="text-gray-600 text-xs">No comments yet</p>
        )}
      </div>
      <div className="mt-3 space-y-2">
        <textarea
          value={commentText}
          onChange={(e) => onCommentTextChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onAddComment() } }}
          placeholder="Add a comment..."
          rows={3}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white placeholder-gray-500 resize-none focus:outline-none focus:border-indigo-500"
        />
        <button
          onClick={onAddComment}
          disabled={commentLoading || !commentText.trim()}
          className="w-full px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-xs text-white font-medium disabled:opacity-50 transition-colors"
        >
          {commentLoading ? 'Posting...' : 'Add Comment'}
        </button>
      </div>
    </div>
  )
}
