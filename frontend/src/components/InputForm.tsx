import { useEffect, useState } from "react";
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
            disabled={isLoading}
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
            disabled={isLoading}
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-SansMono400">Note:</label>
          <textarea
            name="note"
            rows={2}
            value={formData.note}
            onChange={handleChange}
            className="w-full border-b border-black bg-transparent focus:outline-none placeholder-[#151515] placeholder-opacity-25 py-1"
            placeholder="Enter a descriptive note for better search results"
            disabled={isLoading}
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
          rows={1}
          value={NotesTitle}
          onChange={e => setNotesTitle(e.target.value)}
          className="w-full bg-transparent focus:outline-none placeholder-[#151515] placeholder-opacity-25 py-3  border-b border-black"
          placeholder="Write your extra notes here..."
        />
        <label className="block text-md font-SansMono400 text-[15px] ">Extra Notes:</label>
        <textarea
          rows={2}
          value={extraNote}
          onChange={e => setExtraNote(e.target.value)}
          className="w-full bg-transparent focus:outline-none placeholder-[#151515] placeholder-opacity-25 py-3  border-b border-black"
          placeholder="Write your extra notes here..."
        />
      </div>)}

        <div className="flex justify-center mt-0">
          <button
            type="button"
            className="text-neutral-700 bg-white/20 rounded-full px-4 py-2 flex justify-center items-center gap-1 mt-2  text-sm transition hover:text-black"
            onClick={() => setShowNotes(!showNotes)}
            disabled={isLoading}
          >
            <BsChevronDoubleDown size={12} /> { showNotes ? "Add Bookmarks" : "Add Notes"}
          </button>
        </div>

      {Error ? (
        <div className="pb-0 mb-0 space-y-0">
          <p className="text-red-500 font-SansMono400 text-sm text-center pb-0">{Error}</p>
        </div>
      ) : null}

      <div className={`flex ${showOnlyOne ? 'justify-center' : 'justify-between'} mx-auto ${Error ? "pt-0" : "pt-1"}`}>
        <Button handle={handleClear} text={leftBtnTxt} textColor={BtnTxtClr} iSdisabled={isLoading ?? false} />
        {isLoading ? <LoaderPillars /> : null}
        {showOnlyOne ? null : <Button handle={handleSubmit} text={rightBtnTxt} textColor={BtnTxtClr} IncMinWidth="129px" iSdisabled={isLoading ?? false} />}
      </div>
    </form>
  );
}