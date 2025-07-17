import { useEffect, useState, useRef } from "react";
import Button from "./Button";
import LoaderPillars from "./LoaderPillars";
import { BsChevronDoubleDown } from "react-icons/bs";

interface Props {
  handleSubmit: any,
  handleClear: any,
  formData: FormData,
  handleChange: any
  BtnTxtClr: string
  leftBtnTxt: string,
  rightBtnTxt: string
  showOnlyOne?: boolean;
  Error?: string;
  isLoading?: boolean;
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  extraNote: string;
  setExtraNote: (note: string) => void;
  NotesTitle: string;
  setNotesTitle: (title: string) => void;
}
interface FormData {
  link: string;
  title: string;
  note: string;
}

export default function InputForm({
  handleSubmit,
  handleChange,
  handleClear,
  formData,
  BtnTxtClr,
  leftBtnTxt,
  rightBtnTxt,
  showOnlyOne,
  Error,
  isLoading,
  extraNote,
  setExtraNote,
  NotesTitle,
  setNotesTitle,
  setCurrentTab
}: Props) {
  const [showNotes, setShowNotes] = useState(false);
  const notesTextAreaRef = useRef<HTMLTextAreaElement>(null);
  const titleTextAreaRef = useRef<HTMLTextAreaElement>(null);
  const bookmarkNoteRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-focus on bookmark note area when extension opens (default behavior)
  useEffect(() => {
    if (!showNotes && bookmarkNoteRef.current && !isLoading && !showOnlyOne) {
      // Small delay to ensure DOM is ready
      const timer = setTimeout(() => {
        bookmarkNoteRef.current?.focus();
      }, 200);

      return () => clearTimeout(timer);
    }
  }, [showNotes, isLoading, showOnlyOne]);
  
  // Focus the notes text area when notes tab becomes active
  useEffect(() => {
    if (showNotes && notesTextAreaRef.current && !isLoading && !showOnlyOne) {
      // Small delay to ensure the transition animation completes
      const timer = setTimeout(() => {
        notesTextAreaRef.current?.focus();
      }, 200);

      return () => clearTimeout(timer);
    }
  }, [showNotes, isLoading, showOnlyOne]);

  useEffect(()=>{
    if(showNotes){
      setCurrentTab("notes")
    }else{
      setCurrentTab("submit")
    }
  },[showNotes])


  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {!showNotes ? (<div
        className={`form-input-div space-y-4 transition-all duration-500 ${
          showNotes ? "opacity-0 pointer-events-none " : "opacity-100"
        }`}
      >
        <div className="space-y-1">
          <label className="block text-sm font-SansMono400">Link:</label>
          <input
            type="text"
            name="link"
            autoComplete="off"
            value={formData.link}
            onChange={handleChange}
            className="w-full border-b border-black bg-transparent focus:outline-none  pb-1 placeholder-[#151515] placeholder-opacity-25"
            placeholder="Your link here"
            disabled={isLoading || showOnlyOne}
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-SansMono400">Title:</label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            className="w-full border-b border-black bg-transparent focus:outline-none pb-1 placeholder-[#151515] placeholder-opacity-25"
            placeholder="Your title here"
            disabled={isLoading || showOnlyOne}
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-SansMono400">Note:</label>
          <textarea
            ref={bookmarkNoteRef}
            name="note"
            rows={2}
            value={formData.note}
            onChange={handleChange}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                if (formData.link.trim() !== "" && formData.title.trim() !== "" && formData.note.trim() !== "") {
                  handleSubmit(e);
                }
              }
            }}
            className="w-full border-b border-black bg-transparent focus:outline-none placeholder-[#151515] placeholder-opacity-25 py-1 scrollbar-hide"
            placeholder="Add micro-note for better search results (press Enter to save)"
            disabled={isLoading || showOnlyOne}
          />
        </div>

      </div>) :

      (<div
        className={`space-y-2 transition-all duration-500 w-full pb-1 ${
          showNotes ? "opacity-100 translate-y-0 z-10" : "opacity-0 pointer-events-none -translate-y-10"
        }`}
      >
        <label className="block text-md font-SansMono400 text-[15px] ">Title:</label>
        <textarea
          ref={titleTextAreaRef}
          rows={1}
          value={NotesTitle}
          onChange={e => setNotesTitle(e.target.value)}
          className="w-full bg-transparent focus:outline-none placeholder-[#151515] placeholder-opacity-25 py-3  border-b border-black scrollbar-hide"
          placeholder="Your title here..."
          disabled={isLoading || showOnlyOne}
        />
        <label className="block text-md font-SansMono400 text-[15px] ">Note:</label>
        <textarea
          ref={notesTextAreaRef}
          rows={2}
          value={extraNote}
          onChange={e => setExtraNote(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (NotesTitle.trim() !== "" && extraNote.trim() !== "") {
                handleSubmit(e);
              }
            }
          }}
          className="w-full bg-transparent focus:outline-none placeholder-[#151515] placeholder-opacity-25 py-3  border-b border-black scrollbar-hide"
          placeholder="Write your note here... (Press Enter to save)"
          disabled={isLoading || showOnlyOne}
        />
      </div>)}

        <div className="flex justify-center mt-0">
          {!showOnlyOne && !Error && (
            <button
              type="button"
              className="text-neutral-700 bg-white/20 rounded-full px-4 py-2 flex justify-center items-center gap-1 mt-2  text-sm transition hover:text-black"
              onClick={() => setShowNotes(!showNotes)}
              disabled={isLoading || showOnlyOne}
            >
              <BsChevronDoubleDown size={12} /> { showNotes ? "Add Bookmarks" : "Add Notes"}
            </button>
          )}
        </div>

      {Error ? (
        <div className="pb-0 mb-0 space-y-0">
          <p className="text-red-500 font-SansMono400 text-sm text-center pb-0">{Error}</p>
        </div>
      ) : null}

      <div className={`flex ${showOnlyOne ? 'justify-center' : 'justify-between'} mx-auto ${Error ? "pt-0" : "pt-1"}`}>
        {isLoading ? (
          <div className="flex justify-center w-full">
            <LoaderPillars />
          </div>
        ) : (
          <>
            <Button handle={handleClear} text={leftBtnTxt} textColor={BtnTxtClr} iSdisabled={false} />
            {showOnlyOne ? null : <Button handle={handleSubmit} text={rightBtnTxt} textColor={BtnTxtClr} IncMinWidth="129px" iSdisabled={false} />}
          </>
        )}
      </div>
    </form>
  );
}