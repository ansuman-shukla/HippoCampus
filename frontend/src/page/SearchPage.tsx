import Button from "../components/Button";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import ColorChangingSpinner from "../components/Loader";
import { GoBookmark } from "react-icons/go";
import { MdEditNote } from "react-icons/md";


interface Props {
    Quote: string;
}



export default function SearchPage({ Quote }: Props) {
    const Navigate = useNavigate();
    const [query, setQuery] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isError, setisError] = useState<boolean>(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const [activeTab, setActiveTab] = useState("All");
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [showSuggestion, setShowSuggestion] = useState(true);

    // const tabs = ["All", "Bookmarks", "Notes"];

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => {
            setShowSuggestion(false);
        }, 3500);

        return () => clearTimeout(timer);
    }, []);

    const handleSearch = () => {
        setIsLoading(true);
        chrome.runtime.sendMessage({ action: "search", query: query, type: activeTab, cookies: localStorage.getItem("access_token") },
            (response) => {
                if (response) {
                    if (response.data?.detail === "Search failed: No documents found matching query") {
                        Navigate("/response", { state: { data: [] } });
                        return;
                        setIsLoading(false);
                    } else {
                        console.log("The response is:", response.data);
                        const responseArray = response.data.map((item: any) => ({
                            title: item.metadata.title,
                            url: item.metadata.source_url,
                            content: item.metadata.note,
                            date: item.metadata.date,
                            ID: item.metadata.doc_id,
                            type: item.metadata.type
                        }));
                        Navigate("/response", { state: { data: responseArray, Query: query } });
                    }


                } else {
                    setIsLoading(false);
                    console.error("API Error:", response.error);
                }
            }
        )

    };
    const handleSearchAll = () => {
        setIsLoading(true);
        chrome.runtime.sendMessage({ action: "searchAll", cookies: localStorage.getItem("access_token") },
            (response) => {
                if (response) {
                    if (response.data?.detail === "Search failed: No documents found matching query") {
                        console.log("No documents found matching query");
                        Navigate("/response", { state: { data: [] } });
                        setIsLoading(false);
                        return;

                    } else {
                        const linksArray = response.links.map((item: any) => ({
                            title: item.title,
                            url: item.source_url,
                            content: item.note,
                            date: item.date,
                            ID: item.ID,
                            type: item.type
                        }));
                        const notesArray = response.notes.map((item: any) => ({
                            title: item.title,
                            content: item.note,
                            date: item.date,
                            ID: item.ID,
                            type: item.type
                        }));
                        console.log("The links array is from search all: ", linksArray);
                        console.log("The notes array is from search all:", notesArray);
                        const responseArray = [...linksArray, ...notesArray];
                        Navigate("/response", { state: {data: responseArray, Query: " ", isSearchAll:true} });
                    }


                } else {
                    setIsLoading(false);
                    console.error("API Error:", response.error);
                }
            }
        )

    };




    return (
        <>

                <div className="max-w-md bg-white rounded-lg px-10 w-[420px] h-[500px] flex flex-col  justify-between py-10 border border-black">
                    <div className=" flex flex-col gap-2 ">
                    <div className="relative flex border-black border-[1.5px] rounded-full px-1 py-1 justify-between min-h-[43px]
                font-SansText400">
                        <input
                            ref={inputRef}
                            type="text"
                            placeholder={isFilterOpen ? "" : `SEARCH FOR ${activeTab==="All" ? "BOOMARKS AND NOTES" : activeTab.toLocaleUpperCase()}`}
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    if (query.length < 3) {
                                        setisError(true)
                                    }
                                    else {
                                        handleSearch();
                                    }
                                }
                            }}
                            className="bg-transparent focus:outline-none text-black placeholder:text-[11px] placeholder:text-black w-[80%]
                            font-SansText400 pb-[1px] placeholder:tracking-widest
                            placeholdder-opacity-25 transition-all duration-300 ease-in-out"
                        />

                        {isLoading ? (
                            <div>
                            <ColorChangingSpinner />
                            </div>
                        ) :
                            // <BiSearchAlt2 className="cursor-pointer" size={24} opacity={(query.length > 0) ? 1 : 0.4} onClick={(query.length > 3) ? handleSearch : undefined } />
                            <>
                            <div className="relative">
                                <button
                                onClick={() => setIsFilterOpen(!isFilterOpen)}
                                className="bg-black h-full rounded-full">
                                    {activeTab === "All" && <p className="text-white px-2 py-1 font-SansText400 tracking-widest">ALL</p>}
                                    {activeTab === "Bookmark" && <GoBookmark size={18} color="white" className="w-[32px]"/>}
                                    {activeTab === "Note" && <MdEditNote size={18} color="white" className="w-[32px]" />}
                                </button>

                                {showSuggestion && (
                                    <motion.div
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        transition={{ duration: 0.3 }}
                                        className="fixed bg-[#dcdcdc] text-black right-2 top-[88px] px-4 py-2 rounded-full text-[10px] font-SansText400 tracking-wider whitespace-nowrap z-10"
                                    >
                                        click here to filter
                                        <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-[#dcdcdc] rotate-45"></div>
                                    </motion.div>
                                )}
                            </div>
                            </>
                            }
                    </div>
                </div>

                {isFilterOpen && (
                    <>
                    <motion.div
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 50 }}
                    transition={{ duration: 0.3, ease: "spring" }}


                    className=" fixed justify-center items-center left-[46px] top-[41.5px] h-[42px] rounded-full  flex gap-2 font-SansText400 tracking-widest ">
                        <button onClick={() => (setActiveTab("All"), setIsFilterOpen(false))}
                            className={` ${activeTab === "All" ? "bg-lime-300  px-4 py-2 text-gray-800 shadow-sm" : "text-gray-600 hover:text-gray-800 pl-[5px]"} max-h-[90%]  rounded-full`}
                            >ALL</button>
                        <button
                        className={` ${activeTab === "Bookmark " ? "bg-lime-300 px-4 py-2 text-gray-800 shadow-sm" : "text-gray-600 hover:text-gray-800 "} max-h-[90%]  rounded-full`}

                        onClick={() => (setActiveTab("Bookmark"), setIsFilterOpen(false))}>BOOKMARKS</button>
                        <button
                        className={` ${activeTab === "Note" ? "bg-lime-300 px-4 py-2 text-gray-800 shadow-sm" : "text-gray-600 hover:text-gray-800 "} max-h-[90%]  rounded-full `}

                        onClick={() => (setActiveTab("Note"), setIsFilterOpen(false))}>NOTES</button>
                    </motion.div>

                    </>
                )}





                <div className={`font-NanumMyeongjo  text-4xl text-center ${isError ? "text-red-900" : "text-black"}`}>
                    <motion.h1
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 1.5 }}
                        className="text-center"
                    >"{isError ? "The Query must be atleast 3 characters !" : Quote}"</motion.h1>
                </div>
                <div className="w-[95%] mx-auto flex justify-between items-center">
                    <Button text="HOME" handle={() => Navigate("/submit")} textColor="--primary-white"
                        IncMinWidth="118px" />
                    <Button text="SHOW ALL" handle={handleSearchAll} textColor="--primary-white" />
                </div>
            </div>
        </>
    );
}