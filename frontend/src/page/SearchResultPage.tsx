import React, { useEffect, useRef, useState } from 'react';
import Cards from '../components/Cards';
import Button from '../components/Button';
import { useLocation, useNavigate } from 'react-router-dom';
import '../index.css';
import LoaderPillars from '../components/LoaderPillars';
import ToggleTabs from '../components/toggleTab';

// interface ProcessedResult {
//   title: string;
//   url: string;
//   content: string;
//   date: string;
//   ID: string;
// }

const SearchResponse: React.FC = () => {
  const location = useLocation();
  const responseData = location.state?.data || [];
  const query = location.state?.Query || "";
  const isSearchAll = location.state?.isSearchAll || false;
  const errorMessage = location.state?.error || null;
  const linksArray = location.state?.linksArray || [];
  const notesArray = location.state?.notesArray || [];

  const colors = [
    'bg-custom-orange',
    'bg-custom-light-violet',
    'bg-custom-lime',
    'bg-custom-hot-pink',

    'bg-custom-electric-blue',
    'bg-custom-marigold',
    'bg-custom-bright-purple',
    'bg-custom-neon-green',

    'bg-custom-bright-orange',
    'bg-custom-vivid-blue',
    'bg-custom-lime-yellow',
    'bg-custom-violet',

    'bg-custom-chartreuse',
    'bg-custom-light-pink',
    'bg-custom-electric-lime',
    'bg-custom-blue',

    'bg-custom-brownish-orange',
    'bg-custom-green',
    'bg-custom-bright-yellow',
    'bg-custom-yellow'
  ];

  const currentIndex = useRef(0);
  const getNextColor = () => {
    const color = colors[currentIndex.current];
    currentIndex.current = (currentIndex.current + 1) % colors.length;
    return color;
  };

  interface CardType {
    key: number;
    title: string;
    fullDescription: string;
    bgColor: string;
    RedirectUrl: string;
    date: string;
    ID: string;
    type: string;
    isSearchAll: boolean;
    activeTab: string;

  }

  const [Card, setCards] = useState<CardType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [DeleteClicked, setDeleteClicked] = useState<boolean>(false);
  const [confirmDelete, setConfirmDelete] = useState<boolean>(false);
  const [DeleteSuccess, setDeleteSuccess] = useState<boolean>(false);
  const [filteredBrowserBookmarks, setFilteredBrowserBookmarks] = useState<Array<{ url: string, title: string }>>([]);
  const [activeTab, setActiveTab] = useState("All");
  const tabs = ["All", "Bookmark", "Note"];

  const allBookmarks: string[] = [];

  useEffect(()=>{
    console.log("The active tab is:", activeTab);
  },[activeTab])

  useEffect(() => {
    const getAllBookmarks = () => {
      if (!chrome.bookmarks) {
        console.error("chrome.bookmarks API is not available.");
        return;
      }

      // chrome.bookmarks.getTree((bookmarkTreeNodes) => {
      //     const allBookmarks: Array<{ url: string, title: string }> = [];

      //     const extractBookmarks = (nodes: chrome.bookmarks.BookmarkTreeNode[]) => {
      //         for (const node of nodes) {
      //             if (node.url) {
      //                 const url = node.url;
      //                 allBookmarks.push({
      //                     url: node.url,
      //                     title: node.title || url.split("/").pop() || url 
      //                 });
      //             }
      //             if (node.children) extractBookmarks(node.children);
      //         }
      //     };

      //     extractBookmarks(bookmarkTreeNodes);

      //     const newCards = allBookmarks.map((item, index) => ({
      //         key: Card.length + index + 1,
      //         title: item.title, 
      //         fullDescription: item.url,
      //         bgColor: randomColor()
      //     }));

      //     setCards(prev => [...prev, ...newCards]);


      // });

      if (responseData) {
        if (responseData.length === 0) {
          return;
        }
        console.log("The query is:", query);
        console.log("The responseData items:", responseData);
        const newCards = responseData.map((item: any, index: number) => ({
          key: Card.length + index + 1,
          title: item.title,
          fullDescription: (item.content === "" ? "No Description" : item.content),
          bgColor: getNextColor(),
          RedirectUrl: item.url,
          date: item.date ?
            new Date(item.date).toLocaleDateString("en-GB", {
              day: "2-digit",
              month: "long",
              year: "numeric",
            })

            : "No Date",
          ID: item.ID,
          type: item.type,
          isSearchAll: isSearchAll,
          activeTab: activeTab


        }

        ));
        console.log("The newCards after mapping:", newCards);
        setCards(newCards);
      }else if(linksArray && notesArray){
        console.log("The links array is:", linksArray);
        console.log("The notes array is:", notesArray);
        const newCards = [...linksArray, ...notesArray].map((item: any, index: number) => ({
          key: Card.length + index + 1,
          title: item.title,
          fullDescription: (item.content === "" ? "No Description" : item.content),
          bgColor: getNextColor(),
          RedirectUrl: item.url,
          date: item.date ?
            new Date(item.date).toLocaleDateString("en-GB", {
              day: "2-digit",
              month: "long",
              year: "numeric",
            })

            : "No Date",
          ID: item.ID,
          type: item.type,
          isSearchAll: isSearchAll,
          activeTab: activeTab
        }

        ));
        console.log("The newCards from linksArray/notesArray:", newCards);
        setCards(newCards);
      }

      if (!chrome.bookmarks || !query) {
        setFilteredBrowserBookmarks([]);
        return;
      }

      chrome.bookmarks.getTree((bookmarkTreeNodes) => {
        const matches: Array<{ url: string, title: string }> = [];
        const lowerQuery = query.toLowerCase();

        const extractAndFilter = (nodes: chrome.bookmarks.BookmarkTreeNode[]) => {
          const allBrowserBookmarks = nodes.map((node) => ({
            url: node.url,
            title: node.title || node.url && node.url.split("/").pop() || node.url
          }));
          console.log("All bookmarks from chrome: ", allBrowserBookmarks);
          for (const node of nodes) {
            if (node.url && (
              node.title.toLowerCase().includes(lowerQuery) ||
              node.url.toLowerCase().includes(lowerQuery)
            )) {
              console.log("the node is after checking  :", node)
              matches.push({
                url: node.url,
                title: node.title || node.url.split("/").pop() || node.url
              });
              console.log("now the matches are:", matches);
            }
            if (node.children) extractAndFilter(node.children);
          }
        };

        extractAndFilter(bookmarkTreeNodes);
        setFilteredBrowserBookmarks(matches);

      });

    };

    getAllBookmarks();
  }, allBookmarks);


  useEffect(() => {
    console.log("Filtered browser bookmarks: ", filteredBrowserBookmarks);
  }, [filteredBrowserBookmarks]);

  const handleDelete = () => {
    setIsLoading(true);
    if (selectedIndex !== null) {
      const cardToDelete = Card[selectedIndex];
      console.log("=== DELETE DEBUG ===");
      console.log("selectedIndex:", selectedIndex);
      console.log("cardToDelete:", cardToDelete);
      console.log("cardToDelete.ID:", cardToDelete.ID);
      console.log("Card array:", Card);
      console.log("==================");
      
      const isNote = cardToDelete.type === "Note";
      const action = isNote ? "deleteNote" : "delete";
      
      chrome.runtime.sendMessage({ action: action, query: cardToDelete.ID }, (response) => {
        if (response && response.success) {
          // Successfully deleted from backend, now remove from UI
          setCards(prevCards => prevCards.filter((_, index) => index !== selectedIndex));
          setSelectedIndex(null);
          setDeleteSuccess(true);
          setIsLoading(false);
          setConfirmDelete(true);
          
          console.log(`Successfully deleted ${isNote ? 'note' : 'bookmark'}:`, cardToDelete);
        } else {
          console.error("Delete failed:", response?.error);
          setDeleteSuccess(false);
          setIsLoading(false);
          setConfirmDelete(true);
        }
      });
    } else {
      setIsLoading(false);
    }
  }



  const Navigate = useNavigate();

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);



  return (
    <div

      style={{ backgroundColor: responseData.length === 0 ? 'var(--primary-red)' : 'var(--primary-white)' }}

      className={`relative max-w-md  rounded-lg w-[420px] h-[500px] flex flex-col justify-center border border-black py-0 overflow-hidden`}>
      {Card.length === 0 ? (
        <div className='text-center px-6'>
          <p className='text-2xl black mb-3 pb-7 nyr-semibold'>
            {errorMessage ? 'Search Error' : 'Oops ! No items found'}
          </p>
          {errorMessage && (
            <p className='text-lg text-gray-700 mb-4 nyr'>
              {errorMessage}
            </p>
          )}
          {query && !errorMessage && (
            <p className='text-sm text-gray-600 nyr'>
              No results found for "{query}"
            </p>
          )}
        </div>
      ) : (<>
      
        {isSearchAll && selectedIndex === null && 
        <ToggleTabs 
        tabs={tabs}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        />

        }
      
      <div className={` 
        
        ${selectedIndex === null
          ? `overflow-y-scroll py-3 ${isSearchAll ? 'pt-[62px]' : ''} pb-[89px] px-3 `
          : 'overflow-y-scroll py-0 px-0 cursor-default'}
        [&::-webkit-scrollbar]:hidden w-[100%] h-[100%]`}>
        {selectedIndex === null
          ?
          Card.map((card, index) => (
            <Cards
              key={index}
              title={card.title}
              description={card.fullDescription}
              bgColor={card.bgColor}
              onClick={() => {
                setSelectedIndex(index);
                setConfirmDelete(false);
                setDeleteSuccess(false);
              }}
              isSelected={false}
              RedirectUrl={card.RedirectUrl}
              date={card.date}
              confirmDelete={confirmDelete}
              setDeleteClicked={setDeleteClicked}
              isSearchAll={isSearchAll && activeTab === "All"}
              type={card.type}
              activeTab={activeTab}
            />
          )

          )
          : (

            DeleteClicked ?
              <p className='nyr flex justify-center items-center bg-[var(--primary-red)] text-2xl text-center text-black
              w-[100%] h-[90%]'>Are you sure you want to delete this item?</p>
              :
              confirmDelete ?
                isLoading ?
                  <div className='flex justify-center items-center w-full h-[90%] bg-[var(--primary-red)]'>
                    <LoaderPillars />
                  </div>
                  :
                  DeleteSuccess ?
                    <p className='nyr flex justify-center items-center bg-[var(--primary-green)] text-2xl text-center text-black
            w-[100%] h-[90%]'>Item Deleted Successfully!</p> :
                    <p className='nyr flex justify-center items-center bg-[var(--primary-red)] text-2xl text-center text-black  
            w-[100%] h-[90%]'>Failed to delete item!</p>
                :

                <Cards
                  title={Card[selectedIndex].title}
                  description={Card[selectedIndex].fullDescription}
                  bgColor={Card[selectedIndex].bgColor}
                  onClick={() => null}
                  isSelected={true}
                  RedirectUrl={Card[selectedIndex].RedirectUrl}
                  date={Card[selectedIndex].date}
                  confirmDelete={confirmDelete}
                  setDeleteClicked={setDeleteClicked}
                  isSearchAll={isSearchAll && activeTab === "All"}
                  type={Card[selectedIndex].type}
                  activeTab={activeTab}
                />



          )}
          { filteredBrowserBookmarks.length > 0 && selectedIndex === null && activeTab === "All" && <div>
          {filteredBrowserBookmarks.length > 0  && selectedIndex === null && <h1 className='text-center text-[20px] black mt-2 pb-2 nyr-semibold font-medium'>Browser Bookmarks</h1> }
          {filteredBrowserBookmarks.length > 0  && selectedIndex === null && filteredBrowserBookmarks.map((item, index) => (
            <Cards
              key={index}
              title={item.title}
              description={"No description, link: " + item.url}
              bgColor={getNextColor()}
              onClick={() => window.open(item.url)}
              isSelected={false}
              RedirectUrl={item.url}
              date={""}
              confirmDelete={confirmDelete}
              setDeleteClicked={setDeleteClicked}
              isSearchAll={isSearchAll && activeTab === "All"}
              type={""}
              activeTab={activeTab}
            />
          ))}
        </div>}
      </div>
        
      </>

      )}


      <div className="absolute bottom-0 rounded-b-lg w-full min-h-[90px] flex items-center justify-between px-10 bg-white border-t border-black">
        <Button
          text={DeleteClicked ? "NO" : 'BACK'}
          handle={() => {
            if (DeleteClicked) {
              setDeleteClicked(false);
            } else {

              if (selectedIndex === null) Navigate("/search");
              else setSelectedIndex(null);
              setConfirmDelete(false);
              setDeleteSuccess(false);
            }
          }}
          textColor='--primary-white'
        />
        <Button
          text={DeleteClicked ? "YES" : 'HOME'}
          handle={() => {
            if (DeleteClicked) {
              handleDelete();
              setDeleteClicked(false);
              setConfirmDelete(true);
            } else {
              Navigate("/submit");
            }
          }}
          textColor='--primary-white'
        />
      </div>
    </div>
  );
};

export default SearchResponse;