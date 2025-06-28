As a python pioneer expert analyze the page handlers below using serena mcp to help you as well. Carefully analyze these handlers, then compare it to my fansale_check.py. give a carefull thought and analyze together with serena mcp and analyze if these handlers allow both of you to create a better system, or if the current system won't be improved that drastically. carefully think and then decide if the script needs to be refactored and updated using the new. Think what these handlers are and how to use them in the best possible way for automatic ticket reservation and then think on if and if so how to implemnent this. But first analyze and decide before proceeding

**Fansale Handlers I have found**
{<div data-offer-id="9788938" data-qa="ticketToBuy" data-splitting-possibilities="1" data-splitting-possibility-prices="139.15" data-fairdeal="true" data-certified="true" data-offertype="Prezzo fisso" data-seatdescriptionforarialabel="Ingr. Prato B | Posto Unico" class="EventEntry js-EventEntry EventEntry-isClickable" style="order: 0;">
	<div class="OfferEntry-Left">
		<span class="EventEntryRow EventEntryRow-inDetailB">Quantità</span>
			<span class="EventEntryRow EventEntryRow-inDetailB NumberOfTicketsInOffer">1</span>
	</div>
	<div class="OfferEntry-Overlay js-OfferEntry-Overlay">
		<span class="TicketcheckIcon EventEntryRow-UspIcon DetailBUspIcon DetailBUspIcon-top DetailBUspIcon-right visible-xs js-TicketcheckIcon" title="" role="img" aria-hidden="true"></span>
		<span class="FairDealIcon EventEntryRow-UspIcon DetailBUspIcon DetailBUspIcon-bottom DetailBUspIcon-right visible-xs js-FairDealIcon" title="Fair Deal - I prezzi dei biglietti sono uguali al prezzo originale TicketOne" role="img" aria-hidden="true"></span>
		<div class="OfferEntry-Top" aria-hidden="true">
			<span class="EventEntryRow OfferEntry-SeatDescription visible-md" style="overflow-wrap: break-word;">Ingr. Prato B | Posto Unico</span>
			<span class="EventEntryRow OfferEntry-SeatDescription visible-sm" style="overflow-wrap: break-word;">Ingr. Prato B | Posto Unico</span>
			<span class="EventEntryRow OfferEntry-SeatDescription visible-xs" style="overflow-wrap: break-word;">Ingr. Prato B | Posto Unico</span>
		</div>
		<div class="OfferEntry-Bottom">
			<div class="js-OfferEntry-Bottom" aria-hidden="true">
				<span class="OfferEntry-PurchaseTypeAndPrice js-OfferEntry-PurchaseTypeAndPrice"> 
						<span title="L'offerta può essere acquistata direttamente.">Prezzo fisso</span>
					<span class="OfferEntry-PriceSmall"><span class="CurrencyAndMoneyValueFormat"><span class="currencyFormat">€</span> <span class="moneyValueFormat">139,15</span></span></span>
				</span>
			</div>
			<div class="EventEntryRow EventEntry-Icon EventEntry-Icon-inDetailB  hidden-xs" aria-hidden="true">
				<span class="TicketcheckIcon EventEntryRow-UspIcon EventEntryRow-UspIcon-inDetailB js-TicketcheckIcon" title="" role="img" aria-hidden="true"></span>
				<span class="FairDealIcon EventEntryRow-UspIcon EventEntryRow-UspIcon-inDetailB ml0 js-FairDealIcon" title="Fair Deal - I prezzi dei biglietti sono uguali al prezzo originale TicketOne" role="img" aria-hidden="true"></span>
			</div>
		</div>
			<span class="EventEntryRow EventEntry-Link OfferEntry-Link">
				<a href="/tickets/all/1/458554/17844388%3FofferId=9788938?ptc=1" data-track="" aria-label="Ingr. Prato B | Posto Unico, Prezzo fisso € 139,15, Fair Deal Offer, EVENTIM Ticketcheck Offer" role="button" id="detailBShowOfferButton-9788938" class="Button-inOfferEntryList js-Button-inOfferEntryList Button-onlyArrow Button"><span class="UsefulSvgIcon-yellow_arrow_right Button-ArrowIcon" aria-label="Visualizza"></span></a>
			</span>
	</div>
</div>}


this above source i got earlier using inspect in chrome is of the first page where tickets are shown. In this example there is only 1 prato b ticket available.
Then after pressing that ticket with a click it takes you to anothe page with an overview. there is a yellow button that you need to press with this source code 
{<button type="button" data-track="" class="js-checkBarcodesForAutomatedReprint js-detailCSubmitButton Button-super Button-superDetailC Button" data-qa="buyNowButton">Acquista</button>}

After pressing that, it can either automatically lets you go to the checkout page where the ticket is being reserved, or it can sometimes trigger a captcha. There is never a need to log in beforehand.



